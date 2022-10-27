<script>
    import Tile from "./Tile";
    import { gettext } from "../lib/utils";

    import forumImg from "./img/Support Forum.svg";
    import kbImg from "./img/Support Articles.svg";
    import l10nImg from "./img/Localization.svg";
    import socialImg from "./img/Social Support.svg";
    import storeImg from "./img/Play Store.svg";

    export let location;
</script>

<section class="mzp-l-content">
    <h2>
        {#if location}
            {gettext("Other ways to contribute")}
        {:else}
            {gettext("Pick a way to contribute")}
        {/if}
    </h2>
    <nav>
        <ul>
            {#if location?.pathname != "/forum"}
                <Tile to="../forum" img={forumImg}>
                    {gettext("Answer questions in the support forum")}
                </Tile>
            {/if}
            {#if location?.pathname != "/kb"}
                <Tile to="../kb" img={kbImg}>
                    {gettext("Write help articles")}
                </Tile>
            {/if}
            {#if location?.pathname != "/l10n"}
                <Tile to="../l10n" img={l10nImg}>
                    {gettext("Localize support content")}
                </Tile>
            {/if}
            {#if location?.pathname != "/social"}
                <Tile to="../social" img={socialImg}>
                    {gettext("Provide support on social channels")}
                </Tile>
            {/if}
            {#if location?.pathname != "/store"}
                <Tile to="../store" img={storeImg}>
                    {gettext("Respond to mobile store reviews")}
                </Tile>
            {/if}
        </ul>
    </nav>
</section>

<style lang="scss">
    @use "@mozilla-protocol/core/protocol/css/includes/lib" as p;

    section {
        margin-bottom: var(--spacing-lg);
    }

    h2 {
        text-align: center;
        margin: var(--spacing-lg) 0;
    }

    ul {
        display: flex;
        flex-direction: column;
        align-items: stretch;

        @media #{p.$mq-lg} {
            flex-direction: row;
        }

        :global(a) {
            color: inherit;
            text-decoration: none;
            flex: 1;
            min-width: 0;
            margin-bottom: 18px;

            @media #{p.$mq-lg} {
                margin-bottom: 0;
                margin-right: var(--spacing-sm);
            }

            will-change: transform;
            transition: transform 0.1s ease-in-out;
            transform: translateZ(0);
            -webkit-font-smoothing: subpixel-antialiased;

            &:hover {
                color: inherit;
                transform: translateZ(0) scale(1.02);

                @media (prefers-reduced-motion: reduce) {
                    transform: none;
                }
            }

            &:last-of-type {
                margin-bottom: 0;
                margin-right: 0;
            }
        }
    }
</style>
