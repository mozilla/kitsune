/* globals Flux:false */

// The Dispatcher is a singleton.
const Dispatcher = new Flux.Dispatcher();
export default Dispatcher;

Dispatcher.register((event) => {
  if (event.type === undefined) {
    throw new Error([
      "Event with undefined type dispatched!",
      JSON.stringify(event),
    ]);
  }
  console.log("Dispatched event", event.type.name, event);
});
