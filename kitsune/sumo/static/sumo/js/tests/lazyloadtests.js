import {default as chai, expect} from 'chai';
import chaiLint from 'chai-lint';

chai.use(chaiLint);

describe('lazyload', () => {
  it('should load original image', () => {
    $('body').empty().html(`
      <img class="lazy" data-original-src="http://example.com/test.jpg">`
    );
    let $img = $('img');

    $.fn.lazyload.loadOriginalImage($img);
    expect($img.attr('src')).to.equal('http://example.com/test.jpg');
  });
});
