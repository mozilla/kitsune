function fn() {
    // breadcrumbs shadow
    (function() {
        var bc = document.getElementById('breadcrumbs');
        var sh = document.querySelector('#breadcrumbs .shadow');

        function listener(container, shadow) {
            shadow.style.top = container.offsetHeight - 2 + 'px'
        }

        if(bc !== null && sh !== null) {
            window.addEventListener('resize', function() {
                listener(bc, sh)
            }, false);

            listener(bc, sh)
        }
    })();

    // categories nav
    (function() {
        var toggle = document.querySelector('.js-toggle');
        var labels = document.querySelectorAll('.acc label');

        if(toggle !== null) {
            toggle.addEventListener('click', function(e) {
                var target = e.target;

                target.parentNode.classList.toggle('visible')
            })
        }

        if(labels.length) {
            labels = Array.prototype.slice.call(labels);

            labels.forEach(function(item) {
                item.addEventListener('click', function(e) {
                    var target = e.target;
                    var input = target.parentNode.querySelector('input[type="radio"]');

                    if(input !== null) {
                        e.preventDefault();
                        input.checked = !input.checked;
                    }

                })
            })
        }
    })();

    // Slider: swiperjs https://idangero.us/swiper/
    (function(Swiper) {
        if(typeof Swiper !== 'function') return;

        var slider = new Swiper('.swiper-container', {
            slidesPerView: 3,
            spaceBetween: 30,
            navigation: {
                prevEl: '.prev',
                nextEl: '.next'
            },
            breakpoints: {
                960: {
                    slidesPerView: 2
                },
                630: {
                    slidesPerView: 'auto'
                }
            }
        })
    })(window.Swiper);

    // TODO: remove // temp not-helpful
    (function() {
        var containers = document.querySelectorAll('.vote-js');

        for(var i = 0; i < containers.length; i++) {
            init(containers[i])
        }

        function init(container) {
            var notHelpful = container.querySelector('input[name="not-helpful"]');
            var helpful = container.querySelector('input[name="helpful"]');
            var notHelpfulContainer = container.querySelector('.not-helpful-container');
            var helpfulContainer = container.querySelector('.helpful-container');
            var submit = null;

            function clear(arr) {
                arr
                    .filter(Boolean)
                    .forEach(function(item) {
                        item.classList.remove('visible');
                    })
            }

            function listener(e, container) {
                e.preventDefault();
                clear([notHelpfulContainer, helpfulContainer]);
                container.classList.add('visible');
            }

            if(helpfulContainer !== null && helpfulContainer !== null) {
                submit = notHelpfulContainer.querySelector('input[type="submit"]');

                if(submit !== null) {
                    submit.addEventListener('click', function(e) {
                        listener(e, helpfulContainer)
                    })
                }
            }

            if(notHelpful !== null && notHelpfulContainer !== null) {
                notHelpful.addEventListener('click', function(e) {
                    listener(e, notHelpfulContainer)
                }, false)
            }

            if(helpful !== null && helpfulContainer !== null) {
                helpful.addEventListener('click', function(e) {
                    listener(e, helpfulContainer)
                }, false)
            }
        }
    })();

    // TODO: remove // temp search related articles
    (function() {
        var search = document.getElementById('search-q2');
        var results = document.querySelector('.search-form-large .search-results');
        var visible = 'visible';

        if(search !== null && results !== null) {
            search.setAttribute('autocomplete', 'off');
            search.addEventListener('input', listener);
            document.addEventListener('click', hideResults, false);

            function hideResults() {
                results.classList.remove(visible)
            }

            function listener(e) {
                var target = e.target;

                if(target.value.length > 0) {
                    results.classList.add(visible)
                } else {
                    hideResults()
                }
            }
        }
    })();

    // Breadcrumbs dropdown
    (function(window) {
        var liWidth = 250;
        var columnLength = 4;
        var query = 425;

        var breadcrumbs = document.querySelector('.breadcrumbs');
        var containers = document.querySelectorAll('.breadcrumbs > li');
        var dropMenuClass = '.drop-menu ul';
        var stepClass = 'step';

        if(breadcrumbs === null || !containers.length) {
            return
        }

        function hideAll(wrappers) {
            for(var i = 0; i < wrappers.length; i++) {
                document.body.setAttribute('style', '');
                wrappers[i].classList.remove('visible')
            }
        }

        document.addEventListener('click', function(e) {
            e.stopPropagation();

            var target = e.target;

            if(target.classList.contains(stepClass) && !target.parentNode.classList.contains('visible')) {
                hideAll(containers);

                setTimeout(function() {
                    breadcrumbs.classList.add('active');
                    document.body.setAttribute('style', 'overflow: hidden;');
                    target.parentNode.classList.add('visible')
                }, 100)
            } else {
                breadcrumbs.classList.remove('active');

                hideAll(containers)
            }
        }, false);

        initColumns(containers, liWidth, columnLength, dropMenuClass, '.' + stepClass);

        window.addEventListener('resize', function() {
            initColumns(containers, liWidth, columnLength, dropMenuClass, '.' + stepClass)
        });

        function initColumns(list, columnWidth, maxColumnItemsCount, dropMenuCls, stepCls) {
            for(var i = 0; i < list.length; i++) {
                var dropMenu = list[i].querySelector(dropMenuCls);
                var step = list[i].querySelector(stepCls);
                var windowWidth = window.innerWidth;

                if(dropMenu !== null && step !== null) {
                    if(windowWidth > query) {
                        var wantedColumns = Math.ceil(dropMenu.childElementCount / maxColumnItemsCount);
                        var available = Math.floor((windowWidth - step.getBoundingClientRect().left) / columnWidth);
                        var state = Math.min(wantedColumns, available);

                        state = state > 2 ? 3 : state;

                        dropMenu.setAttribute('data-columns', state.toString())
                    }
                }
            }

        }
    })(window);

    // video slider
    (function(Swiper) {
        if(typeof Swiper !== 'function') return;

        var thumbs = document.querySelector('.gallery-thumbs');
        var galleryTop = document.querySelector('.gallery-top');

        if(thumbs !== null && galleryTop !== null) {
            var thumbsSlider = new Swiper(thumbs, {
                spaceBetween: 10,
                slidesPerView: 'auto',
                // freeMode: true,
                watchSlidesVisibility: true,
                watchSlidesProgress: true,
                on: {
                    click: function() {
                        var videos = galleryTop.querySelectorAll('video');

                        for(var i = 0; i < videos.length; i++) {
                            videos[i].pause()
                        }
                    }
                }
            });

            var galleryTopSlider = new Swiper(galleryTop, {
                spaceBetween: 10,
                wrapperClass: 'gallery-wrapper',
                slideClass: 'gallery-slide',
                slidesPerView: 1,
                allowTouchMove : false,
                thumbs: {
                    swiper: thumbsSlider
                }
            })
        }
    })(window.Swiper);
}

function ready(fn) {
    if (document.attachEvent ? document.readyState === "complete" : document.readyState !== "loading"){
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}

ready(fn);
