/*global window, document, jQuery, gettext */
/*
    Marky, the markup toolbar builder

    Usage:
    <script type="text/javascript">
        // Create the simple toolbar (used in Forums and Questions)
        Marky.createSimpleToolbar('#toolbar-container-id', '#textarea-id');

        // or, create the full toolbar (used in the Knowledgebase)
        Marky.createFullToolbar('#toolbar-container-id', '#textarea-id');

        //or, create a custom toolbar.
        Marky.createFullToolbar('#toolbar-container-id', '#textarea-id', [
            new Marky.SimpleButton(
                gettext('Bold'), "'''", "'''", gettext('bold text'),
                'btn-bold'),
            new Marky.SimpleButton(
                gettext('Italic'), "''", "''", gettext('italic text'),
                'btn-italic')
        ]);
    </script>

*/
(function($, gettext, document){

var Marky = {
    createSimpleToolbar: function(toolbarSel, textareaSel) {
        var SB = Marky.SimpleButton,
            buttons = [
            new SB(gettext('Bold'), "'''", "'''", gettext('bold text'),
                   'btn-bold'),
            new SB(gettext('Italic'), "''", "''", gettext('italic text'),
                   'btn-italic'),
            new Marky.Separator(),
            new Marky.LinkButton(),
            new Marky.Separator(),
            new SB(gettext('Numbered List'), '# ', '',
                   gettext('Numbered list item'), 'btn-ol', true),
            new SB(gettext('Bulleted List'), '* ', '',
                   gettext('Bulleted list item'), 'btn-ul', true)
        ];
        Marky.createCustomToolbar(toolbarSel, textareaSel, buttons);
    },
    createFullToolbar: function(toolbarSel, textareaSel) {
        var SB = Marky.SimpleButton,
            buttons = Marky.allButtonsExceptShowfor();
        buttons.push(new Marky.Separator());
        buttons.push(new Marky.ShowForButton());
        Marky.createCustomToolbar(toolbarSel, textareaSel, buttons);
    },
    createCustomToolbar: function(toolbarSel, textareaSel, partsArray) {
        var $toolbar = $(toolbarSel || '.editor-tools'),
            textarea = $(textareaSel || '#reply-content, #id_content')[0];
        for (var i=0, l=partsArray.length; i<l; i++) {
            $toolbar.append(partsArray[i].bind(textarea).node());
        }
    },
    allButtonsExceptShowfor: function() {
        var SB = Marky.SimpleButton;
        return [
            new SB(gettext('Bold'), "'''", "'''", gettext('bold text'),
                   'btn-bold'),
            new SB(gettext('Italic'), "''", "''", gettext('italic text'),
                   'btn-italic'),
            new Marky.Separator(),
            new Marky.LinkButton(),
            new Marky.MediaButton(),
            new Marky.Separator(),
            new SB(gettext('Numbered List'), '# ', '',
                   gettext('Numbered list item'), 'btn-ol', true),
            new SB(gettext('Bulleted List'), '* ', '',
                   gettext('Bulleted list item'), 'btn-ul', true),
            new Marky.Separator(),
            new SB(gettext('Heading 1'), '=', '=', gettext('Heading 1'),
                   'btn-h1', true),
            new SB(gettext('Heading 2'), '==', '==', gettext('Heading 2'),
                   'btn-h2', true),
            new SB(gettext('Heading 3'), '===', '===', gettext('Heading 3'),
                   'btn-h3', true)
        ];
    }
};


/*
 * A simple button.
 * Note: `everyline` is a boolean value that says whether or not the selected
 *       text should be broken into multiple lines and have the markup applied
 *       to each line or not. Default is false (do not apply this behavior).
 *       `classes` is a list of classes to include in the output
 */
Marky.SimpleButton = function(name, openTag, closeTag, defaultText,
                              classes, everyline) {
    this.name = name;
    this.classes = '';
    this.openTag = openTag;
    this.closeTag = closeTag;
    this.defaultText = defaultText;
    this.everyline = everyline;
    if (undefined !== classes) {
        this.classes = classes;
    }

    this.html = '<button class="markup-toolbar-button" />';
};

Marky.SimpleButton.prototype = {
    // Binds the button to a textarea (DOM node).
    bind: function(textarea) {
        this.textarea = textarea;
        return this;
    },
    // Renders the html.
    render: function() {
        var $out = $(this.html).attr({
            title: this.name,
            innerHTML: this.name
        });
        $out.addClass(this.classes);
        return $out;
    },
    // Gets the DOM node for the button.
    node: function() {
        var me = this,
            $btn = this.render();
        $btn.click(function(e) {
            me.handleClick(e);
        });
        return $btn[0];
    },
    // Get selected text
    getSelectedText: function() {
        var selText = '';
        if(document.selection && document.selection.createRange) {
            // IE/Opera
            selText = document.selection.createRange().text;
        } else if(this.textarea.selectionStart ||
                  this.textarea.selectionStart == '0') {
            // Firefox/Safari/Chrome/etc.
            selText = this.textarea.value.substring(
                this.textarea.selectionStart, this.textarea.selectionEnd);
        }
        return selText;
    },
    // Handles the button click.
    handleClick: function(e) {
        var selText, selStart, selEnd, splitText, range,
            textarea = this.textarea,
            scrollTop = $(textarea).scrollTop();
        textarea.focus();

        if (document.selection && document.selection.createRange) {
            // IE/Opera
            range = document.selection.createRange();
            selText = range.text;
            if(!selText.length) {
                selText = this.defaultText;
            }

            if(this.everyline && -~selText.indexOf('\n')) {
                splitText = this._applyEveryLine(this.openTag, this.closeTag,
                                                 selText);
                range.text = splitText.join('\n');
            } else {
                range.text = this.openTag + selText + this.closeTag;

                if(range.moveStart) {
                    range.moveStart('character', (-1 * this.openTag.length) -
                                                 selText.length);
                    range.moveEnd('character', (-1 * this.closeTag.length));
                }
            }

            range.select();
        } else if (textarea.selectionStart || textarea.selectionStart == '0') {
            // Firefox/Safari/Chrome/etc.
            selStart = textarea.selectionStart;
            selEnd = textarea.selectionEnd;
            selText = textarea.value.substring(selStart, selEnd);
            if(!selText.length) {
                selText = this.defaultText;
            }

            if(this.everyline && -~selText.indexOf('\n')) {
                splitText = this._applyEveryLine(this.openTag, this.closeTag,
                                                 selText).join('\n');
                textarea.value =
                    textarea.value.substring(0, textarea.selectionStart) +
                    splitText +
                    textarea.value.substring(textarea.selectionEnd);

                textarea.selectionStart = selStart;
                textarea.selectionEnd = textarea.selectionStart +
                                        splitText.length;
            } else {
                textarea.value =
                    textarea.value.substring(0, textarea.selectionStart) +
                    this.openTag + selText + this.closeTag +
                    textarea.value.substring(textarea.selectionEnd);

                textarea.selectionStart = selStart + this.openTag.length;
                textarea.selectionEnd = textarea.selectionStart +
                                        selText.length;
            }
        }
        $(textarea).scrollTop(scrollTop);
        e.preventDefault();
        return false;
    },
    _applyEveryLine: function(opentag, closetag, block) {
        return $.map(block.split('\n'), function(line) {
            return (line.replace(/\s+/, '').length ?
                    opentag + line + closetag : line);
        });
    }
};

/*
 * The showfor helper link.
 */
Marky.ShowForButton = function() {
    this.name = gettext('Show for...');
    this.classes = 'btn-showfor';
    this.openTag = '{for}';
    this.closeTag = '{/for}';
    this.defaultText = 'Show for text.';
    this.everyline = false;
    this.tooltip = gettext('Show content only for specific versions of Firefox or operating systems.');

    this.html = interpolate('<a class="markup-toolbar-link" href="#show-for" title="%s">%s</a>',
                            [this.tooltip, this.name]);
};

Marky.ShowForButton.prototype = $.extend({}, Marky.SimpleButton.prototype, {
    // Renders the html.
    render: function() {
        return $(this.html);
    },
    // Gets the DOM node for the button.
    node: function() {
        var me = this,
            $btn = this.render();
        $btn.click(function(e) {
            me.openModal(e);
        });
        return $btn[0];
    },
    openModal: function(e) {
        var me = this,
            // TODO: look at using a js template solution (jquery-tmpl?)
            $html = $('<section class="marky">' +
                       '<div class="placeholder"/>' +
                       '<div class="submit"><button type="button"></button>' +
                       '<a href="#cancel" class="kbox-cancel"></a></div>' +
                       '</section>'),
            $placeholder = $html.find('div.placeholder'),
            data = $(this.textarea).data('showfor'),
            kbox;

        $html.find('button').text(gettext('Add Rule')).click(function(e){
            var showfor = '';
            $('#showfor-modal input:checked').each(function(){
                showfor += ($(this).val() + ',');
            });
            me.openTag = '{for ' + showfor.slice(0,showfor.length-1) + '}';
            me.handleClick(e);
            kbox.close();
        });
        $html.find('a.kbox-cancel').text(gettext('Cancel'));
        appendOptions($placeholder, data.versions);
        appendOptions($placeholder, data.oses);

        function appendOptions($ph, options) {
            $.each(options, function(i, value) {
                $ph.append($('<h2/>').text(value[0]));
                $.each(value[1], function(i, value) {
                    $ph.append(
                        $('<label/>').text(value[1]).prepend(
                            $('<input type="checkbox" name="showfor"/>')
                                .attr('value', value[0])
                        )
                    );
                });
            });
        }

        kbox = new KBox($html, {
            title: this.name,
            destroy: true,
            modal: true,
            id: 'showfor-modal',
            container: $('body')
        });
        kbox.open();

        e.preventDefault();
        return false;
    }
});

/*
 * A button separator.
 */
Marky.Separator = function() {
    this.html = '<span class="separator"></span>';
};

Marky.Separator.prototype = {
    node: function() {
        return $(this.html)[0];
    },
    bind: function() {
        return this;
    }
};

/*
 * The link helper.
 */
Marky.LinkButton = function() {
    this.name = gettext('Insert a link...');
    this.classes = 'btn-link';
    this.openTag = '[http://example.com ';
    this.closeTag = ']';
    this.defaultText = gettext('link text');
    this.everyline = false;

    this.origOpenTag = this.openTag;
    this.origCloseTag = this.closeTag;
    this.origDefaultText = this.defaultText;

    this.html = '<button class="markup-toolbar-button" />';
};

Marky.LinkButton.prototype = $.extend({}, Marky.SimpleButton.prototype, {
    // Gets the DOM node for the button.
    node: function() {
        var me = this,
            $btn = this.render();
        $btn.click(function(e) {
            me.openModal(e);
        });
        return $btn[0];
    },
    reset: function() {
        this.openTag = this.origOpenTag;
        this.closeTag = this.origCloseTag;
        this.defaultText = this.origDefaultText;
    },
    openModal: function(e) {
        var me = this,
            // TODO: look at using a js template solution (jquery-tmpl?)
            $html = $(
                '<section class="marky">' +
                '<label>' + gettext('Link text:') + '</label>' +
                '<input type="text" name="link-text" />' +
                '<label>' + gettext('Link target:') + '</label>' +
                '<ol><li><label><input type="radio" name="link-type" value="internal" /> ' +
                gettext('Support article:') + '</label> ' +
                '<input type="text" name="internal" placeholder="' +
                gettext('Enter the name of the article') + '" /></li>' +
                '<li><label><input type="radio" name="link-type" value="external" /> ' +
                gettext('External link:') + '</label> ' +
                '<input type="text" name="external" placeholder="' +
                gettext('Enter the URL of the external link') + '" /></li>' +
                '</ol><div class="submit"><button type="button"></button>' +
                '<a href="#cancel" class="kbox-cancel">' + gettext('Cancel') +
                '</a></div></section>' // whew, yuck!?
            ),
            selectedText = me.getSelectedText(),
            kbox;

        $html.find('li input[type="text"]').focus(function() {
            $(this).closest('li').find('input[type="radio"]').click();
        });

        $html.find('button').text(gettext('Insert Link')).click(function(e){
            // Generate the wiki markup based on what the user has selected
            // (interval vs external links) and entered into the textboxes,
            // if anything.
            var val = $html.find('input[type="radio"]:checked').val(),
                text = $html.find('input[name=link-text]').val(),
                $internal = $html.find('input[name="internal"]'),
                $external = $html.find('input[name="external"]');
            me.reset();
            if (val === 'internal') {
                var title = $internal.val();
                if(title) {
                    if(title === selectedText) {
                        // The title wasn't changed, so lets keep it selected.
                        me.openTag = '[[';
                        me.closeTag = ']]';
                        if (text) {
                            me.closeTag = '|' + text + me.closeTag;
                        }
                    } else {
                        // The title changed, so lets insert link before the cursor.
                        me.openTag = '[[' + title;
                        if (text) {
                            me.openTag += '|' + text;
                        }
                        me.openTag += ']] ';
                        me.closeTag = '';
                        me.defaultText = '';
                    }
                } else {
                    me.openTag = '[[';
                    me.closeTag = ']]';
                    if(text) {
                        me.closeTag = '|' + text + ']]';
                    }
                    me.defaultText = gettext('Knowledge Base Article');
                }
            } else {
                var link = $external.val();
                if (link) {
                    if (link.indexOf('http') != 0) {
                        link = 'http://' + link;
                    }
                    me.openTag = '[' + link + ' ';
                    if (text) {
                        me.openTag += text + '] ';
                        me.closeTag = '';
                        me.defaultText = '';
                    }
                } else if (text) {
                    me.defaultText = text;
                }
            }

            me.handleClick(e);
            kbox.close();
        });

        if (selectedText) {
            // If there user has selected text, lets default to it being
            // the Article Title.
            $html.find('input[name="internal"]').val(selectedText).focus();
        }

        kbox = new KBox($html, {
            title: this.name,
            destroy: true,
            modal: true,
            id: 'link-modal',
            container: $('body')
        });
        kbox.open();

        e.preventDefault();
        return false;
    }
});

/*
 * The media helper.
 */
Marky.MediaButton = function() {
    this.name = gettext('Insert media...');
    this.classes = 'btn-media';
    this.openTag = '';
    this.closeTag = '';
    this.defaultText = gettext('media');
    this.everyline = false;

    this.html = '<button class="markup-toolbar-button" />';
};

Marky.MediaButton.prototype = $.extend({}, Marky.SimpleButton.prototype, {
    // Gets the DOM node for the button.
    node: function() {
        var me = this,
            $btn = this.render();
        $btn.click(function(e) {
            me.openModal(e);
        });
        return $btn[0];
    },
    reset: function() {
        this.openTag = '';
        this.closeTag = '';
        this.defaultText = '';
    },
    openModal: function(e) {
        var me = this,
            $editor = $(me.textarea).closest('.editor'),
            mediaSearchUrl = $editor.data('media-search-url'),
            galleryUrl = $editor.data('media-gallery-url'),
            // TODO: look at using a js template solution (jquery-tmpl?)
            $html = $(
                '<section class="marky">' +
                '<div class="filter"><div class="type">' +
                '<span>' + gettext('Show:') + '</span>' +
                '<ol><li data-type="image" class="selected">' + gettext('Images') + '</li>' +
                '<li data-type="video">' + gettext('Videos') + '</li></ol></div>' +
                '<div class="search"><input type="text" name="q" />' +
                '<button>' + gettext('Search Gallery') + '</button></div></div>' +
                '<div class="placeholder" /><div class="submit">' +
                '<button>' + gettext('Insert Media') + '</button>' +
                '<a href="' + galleryUrl + '#upload" class="upload" target="_blank">' +
                gettext('Upload Media') + '</a>' +
                '<a href="#cancel" class="kbox-cancel">' + gettext('Cancel') + '</a></div>' +
                '</section>'
            ),
            selectedText = me.getSelectedText(),
            mediaType = $html.find('div.type li.selected').data('type'),
            mediaQ = '',
            mediaPage = 1,
            kbox;

        // Handle Images/Videos filter
        $html.find('div.type li').click(function(e) {
            var $this = $(this);
            if(!$this.is('.selected')) {
                $html.find('div.type li.selected').removeClass('selected');
                $this.addClass('selected');
                mediaType = $this.data('type');
                mediaPage = 1;
                updateResults();
            }
            e.preventDefault();
            return false;
        });

        // Handle Search button
        $html.find('div.search button').click(function(e) {
            mediaQ = $html.find('input[name="q"]').val();
            mediaPage = 1;
            updateResults();
            e.preventDefault();
            return false;
        });

        // Handle Upload link
        $html.find('a.upload').click(function(e) {
            // Close the modal. The link itself will open gallery in new tab/window.
            kbox.close();
        });

        //Handle pagination
        $html.delegate('ol.pagination a', 'click', function(e) {
            mediaPage = parseInt($(this).attr('href').split('&page=')[1], 10);
            updateResults();
            e.preventDefault();
            return false;
        });

        // Handle 'Insert Media' button click
        $html.find('div.submit button').click(function(e) {
            // Generate the wiki markup based on what the user has selected.
            me.reset();

            var $selected = $html.find('#media-list > li.selected');
            if ($selected.length < 1) {
                alert(gettext('Please select an image or video to insert.'));
                return false;
            }

            me.openTag = '[[';
            me.openTag += (mediaType == 'image') ? 'Image' : 'Video';
            me.openTag += ':' + $selected.find('a').attr('title') + ']] ';

            me.handleClick(e);
            kbox.close();
        });

        updateResults();

        // Update the media list via ajax call.
        function updateResults(type, q) {
            $html.addClass('processing');
            $.ajax({
                url: mediaSearchUrl,
                type: 'GET',
                data: {type: mediaType, q: mediaQ, page: mediaPage},
                dataType: 'html',
                success: function(html) {
                    $html.find('div.placeholder').html(html);
                    $html.find('#media-list > li').click(function(e) {
                        var $this = $(this),
                            $mediaList = $(this).parent();
                        $mediaList.find('li.selected').removeClass('selected');
                        $this.addClass('selected');
                        e.preventDefault();
                        return false;
                    });
                },
                error: function() {
                    var message = gettext("Oops, there was an error.");
                    $html.find('div.placeholder').html('<div class="msg">' +
                                                  message + '</div>');
                },
                complete: function() {
                    $html.removeClass('processing');
                }
            });
        }

        kbox = new KBox($html, {
            title: this.name,
            destroy: true,
            modal: true,
            id: 'media-modal',
            container: $('body'),
            position: 'none'
        });
        kbox.open();

        e.preventDefault();
        return false;
    }
});

window.Marky = Marky;

}(jQuery, gettext, document));
