<script>
    export let link;
</script>

{#if link}
    <a href={link}><slot /></a>
{:else}
    <slot />
{/if}

<style lang="scss">
    @use "@mozilla-protocol/core/protocol/css/includes/lib" as p;

    a,
    a:visited,
    a:active {
        color: var(--color-heading);
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }

    a:visited {
        background-color: var(--color-link-active-bg);
        font-weight: bold;
    }
</style>
