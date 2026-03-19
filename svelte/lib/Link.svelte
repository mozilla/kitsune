<script>
    import { getContext } from "svelte";

    export let to = "/";

    const { basepath } = getContext("router");

    function resolve(to, basepath) {
        if (to.startsWith("/")) return to;
        if (to === ".." || to === "../") return basepath;
        if (to.startsWith("../")) return basepath + "/" + to.slice(3).replace(/\/$/, "");
        return basepath + "/" + to;
    }

    const href = resolve(to, basepath);
</script>

<a {href}><slot /></a>
