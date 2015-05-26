/* globals Flux:false */

// Dispatchers are singletons.
const AAQDispatcher = new Flux.Dispatcher();

AAQDispatcher.register((action) => {
  console.log('Dispatching action:', action);
});

export default AAQDispatcher;
