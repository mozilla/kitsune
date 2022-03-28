<script>
    import { Link } from "svelte-navigator";

    export let to;
    export let img;
</script>

<Link {to}>
    <li class="zoom-on-hover">
        <img src={img} alt="" />
        <span><slot /></span>
    </li>
</Link>

<style lang="scss">
    li {
        height: 100%;
        background-color: var(--tile-bg);
        box-shadow: var(--tile-shadow);
        border-radius: 4px;

        display: flex;
        align-items: center;
        flex-direction: column;

        font-size: 20px;
        text-align: center;

        img {
            margin: 47px;
            max-width: 136px;
        }

        span {
            margin: var(--spacing-sm);
        }
    }
</style>
