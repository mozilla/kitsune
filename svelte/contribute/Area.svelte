<script>
    import Header from "./Header";
    import Steps from "./Steps";
    import Picker from "./Picker";

    export let area;
    export let images;
    export let steps;
    export let location;
</script>

<svelte:head>
    <title>
        {area} | {gettext("Contribute")} | {gettext("Mozilla Support")}
    </title>
</svelte:head>

<Header {area} {images}>
    <slot />
</Header>

<Steps {...steps} />

<Picker {location} />
