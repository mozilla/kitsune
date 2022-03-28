<script>
    import Header from "./Header";
    import Steps from "./Steps";
    import Picker from "./Picker";

    export let area;
    export let img;
    export let steps;
    export let location;
</script>

<Header {area} {img}>
    <slot />
</Header>

<Steps {...steps} />

<Picker {location} />
