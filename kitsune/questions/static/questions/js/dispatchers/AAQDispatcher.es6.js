/* globals Flux:false */

// Dispatchers are singletons.
const AAQDispatcher = new Flux.Dispatcher();
export default AAQDispatcher;


AAQDispatcher.register((event) => {
  if (event.type === undefined) {
    throw new Error(['Event with undefined type dispatched!', JSON.stringify(event)]);
  }
  console.log('Dispatched event', event.type.name, event);
});
