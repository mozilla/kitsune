import {default as chai, expect} from 'chai';
import React from 'react';
import chaiLint from 'chai-lint';

chai.use(chaiLint);

describe('lazyload', () => {
  it('should load original image', () => {
    let img = <img className="lazy" data-original-src="http://example.com/test.jpg"/>;
    React.render(img, document.body);
    let $img = $('img');

    $.fn.lazyload.loadOriginalImage($img);
    expect($img.attr('src')).to.equal('http://example.com/test.jpg');
  });
});
