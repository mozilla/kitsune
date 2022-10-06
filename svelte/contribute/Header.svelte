<script>
    import { Link } from "svelte-navigator";
    import { srcset, gettext } from "../lib/utils";

    export let area = "";
    export let images;
</script>

<header>
    <div class="mzp-l-content">
        <nav class="breadcrumbs">
            <ol id="breadcrumbs" class="breadcrumbs--list">
                <li><a href="/">{gettext("Home")}</a></li>
                <li>
                    {#if area}
                        <Link to="../">{gettext("Contribute")}</Link>
                    {:else}
                        {gettext("Contribute")}
                    {/if}
                </li>
                {#if area}
                    <li>{area}</li>
                {/if}
            </ol>
        </nav>

        <div class="hero">
            <div class="text"><slot /></div>
            <picture>
                <source
                    srcset={srcset(images[1], images[2])}
                    type="image/webp"
                />
                <img srcset={srcset(images[0])} src={images[0]} alt="" />
            </picture>
        </div>
    </div>
</header>

<style lang="scss">
    @use "@mozilla-protocol/core/protocol/css/includes/lib" as p;

    header {
        background-color: var(--header-bg);
        padding-top: 40px;
    }

    @media #{p.$mq-lg} {
        :global(.breadcrumbs--list) {
            margin-bottom: 0;
        }
    }

    .hero {
        display: flex;
        flex-direction: column-reverse;
        align-items: center;

        @media #{p.$mq-lg} {
            flex-direction: row;
        }

        .text,
        picture,
        img {
            flex: 1;
        }

        img {
            height: 500px;
            object-fit: contain;
            margin-bottom: var(--spacing-md);
        }
    }
</style>
