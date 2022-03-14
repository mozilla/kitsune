<script>
    import { Link } from "svelte-navigator";

    export let to;
</script>

<li>
    <Link {to}><slot /></Link>
</li>

<style lang="scss">
    @use "@mozilla-protocol/core/protocol/css/includes/lib" as p;

    li {
        &::before {
            content: "";
            background: url("protocol/img/icons/reader-mode.svg");
            background-repeat: no-repeat;
            background-size: p.$spacing-md p.$spacing-md;
            padding-left: p.$spacing-lg;
        }
    }
</style>
