<script>
    import { getContext, setContext } from "svelte";

    export let path = "/";

    const { relativePath } = getContext("router");

    const normalizedPath = path === "/" ? "/" : "/" + path.replace(/^\//, "");
    const matches =
        normalizedPath === "/"
            ? relativePath === "/" || relativePath === ""
            : relativePath === normalizedPath ||
              relativePath.startsWith(normalizedPath + "/");

    const location = matches ? { pathname: relativePath } : null;
    setContext("route", { location });
</script>

{#if matches}
    <slot />
{/if}
