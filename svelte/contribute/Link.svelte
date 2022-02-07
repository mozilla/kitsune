<script>
    import { Link } from "svelte-navigator";

    export let to;
</script>

<li>
    <Link {to}><slot /></Link>
</li>
