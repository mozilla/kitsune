function tabsInit() {
  const container = document.querySelector('.tabs')

  // insert "more" button and duplicate the list
  if (container) {
    const primary = container.querySelector('.tabs--list')
    const primaryItems = container.querySelectorAll('.tabs--list > li:not(.tabs--item-more)')
    container.classList.add('is-js-enhanced')


  primary.insertAdjacentHTML('beforeend', `
    <li class="tabs--item-more">
      <button class="tabs--button" type="button" aria-haspopup="true" aria-expanded="false">
        More
      </button>
      <ul class="tabs--dropdown elevation-01">
        ${primary.innerHTML}
      </ul>
    </li>
  `)
  const secondary = container.querySelector('.tabs--dropdown')
  const secondaryItems = secondary.querySelectorAll('li')
  const allItems = container.querySelectorAll('li')
  const moreLi = primary.querySelector('.tabs--item-more')
  const moreBtn = moreLi.querySelector('button')
  moreBtn.addEventListener('click', (e) => {
    e.preventDefault()
    container.classList.toggle('dropdown-is-open')
    moreBtn.setAttribute('aria-expanded', container.classList.contains('dropdown-is-open'))
  })

  // adapt tabs

  const doAdapt = () => {
    // reveal all items for the calculation
    allItems.forEach((item) => {
      item.classList.remove('is-hidden')
    })

    // is-hidden items that won't fit in the Primary
    let stopWidth = moreBtn.offsetWidth
    let hiddenItems = []
    const primaryWidth = primary.offsetWidth
    primaryItems.forEach((item, i) => {
      if(primaryWidth >= stopWidth + item.offsetWidth) {
        stopWidth += item.offsetWidth
      } else {
        item.classList.add('is-hidden')
        hiddenItems.push(i)
      }
    })

    // toggle the visibility of More button and items in Secondary
    if(!hiddenItems.length) {
      moreLi.classList.add('is-hidden')
      container.classList.remove('dropdown-is-open')
      moreBtn.setAttribute('aria-expanded', false)
    }
    else {
      secondaryItems.forEach((item, i) => {
        if(!hiddenItems.includes(i)) {
          item.classList.add('is-hidden')
        }
      })
    }
  }

  doAdapt() // adapt immediately on load
  window.addEventListener('resize', doAdapt) // adapt on window resize

  // is-hidden Secondary on the outside click

  document.addEventListener('click', (e) => {
    let el = e.target
    while(el) {
      if(el === secondary || el === moreBtn) {
        return;
      }
      el = el.parentNode
    }
    container.classList.remove('dropdown-is-open')
    moreBtn.setAttribute('aria-expanded', false)
  })

  }
};

// This is patched here to help the tests locate the referenced function
if (typeof module != 'undefined' && module.exports) {
  module.exports.tabsInit = tabsInit;
}

tabsInit();
