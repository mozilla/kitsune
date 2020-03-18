'use strict';

/**
 * This module is used to load the base KSS builder class needed by this builder
 * and to define any custom CLI options or extend any base class methods.
 *
 * Note: since this builder wants to extend the KssBuilderBaseNunjucks class, it
 * must export a KssBuilderBaseNunjucks sub-class as a module. Otherwise, kss-node
 * will assume the builder wants to use the KssBuilderBaseHandlebars class.
 *
 * This file's name should follow standard node.js require() conventions. It
 * should either be named index.js or have its name set in the "main" property
 * of the builder's package.json. See
 * http://nodejs.org/api/modules.html#modules_folders_as_modules
 *
 * @module kss/builder/nunjucks
 */

const path = require('path');

// We want to extend kss-node's Nunjucks builder so we can add options that
// are used in our templates.
let KssBuilderBaseNunjucks;
try {
  // In order for a builder to be "kss clone"-able, it must use the
  // require('kss/builder/path') syntax.
  KssBuilderBaseNunjucks = require('kss/builder/base/nunjucks');
} catch (e) {
  // The above require() line will always work.
  //
  // Unless you are one of the developers of kss-node and are using a git clone
  // of kss-node where this code will not be inside a "node_modules/kss" folder
  // which would allow node.js to find it with require('kss/anything'), forcing
  // you to write a long-winded comment and catch the error and try again using
  // a relative path.
  KssBuilderBaseNunjucks = require('../base/nunjucks');
}

/**
 * A kss-node builder that takes input files and builds a style guide using Nunjucks
 * templates.
 */
class KssBuilderNunjucks extends KssBuilderBaseNunjucks {
  /**
   * Create a builder object.
   */
  constructor() {
    // First call the constructor of KssBuilderBaseNunjucks.
    super();

    // Then tell kss which Yargs-like options this builder adds.
    this.addOptionDefinitions({
      title: {
        group: 'Style guide:',
        string: true,
        multiple: false,
        describe: 'Title of the style guide',
        default: 'KSS Style Guide'
      }
    });
  }

  // add builder extend
  prepareExtend(templateEngine) {
    this.options.extend.push(path.resolve(__dirname, 'extend'));

    return super.prepareExtend(templateEngine);
  }
}

module.exports = KssBuilderNunjucks;
