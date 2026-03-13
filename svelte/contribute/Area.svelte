<script>
    import { getContext } from "svelte";
    import Header from "./Header";
    import Steps from "./Steps";
    import Picker from "./Picker";
    import { gettext } from "../lib/utils";

    export let area;
    export let images;
    export let steps;

    const { location } = getContext("route");
</script>

<svelte:head>
    <title>
        {area} | {gettext("Contribute")} | {gettext("Mozilla Support")}
    </title>
</svelte:head>

<Header {area} {images}>
    <slot />
</Header>

<Steps {location} {...steps} />
<Picker {location} />
