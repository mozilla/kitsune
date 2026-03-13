<script>
    import { setContext } from "svelte";

    export let basepath = "/";
    export let url = "";

    const currentPath =
        typeof window !== "undefined" ? window.location.pathname : url;

    const relativePath = currentPath.startsWith(basepath)
        ? currentPath.slice(basepath.length) || "/"
        : "/";

    setContext("router", { basepath, relativePath });
</script>

<slot />
