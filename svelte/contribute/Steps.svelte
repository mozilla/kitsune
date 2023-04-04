<script>
    import { queryStore, gql, getContextClient } from "@urql/svelte";
    import Linkable from "./Linkable.svelte";
    import { gettext } from "../lib/utils";
    import { TEACHABLE_URL } from "../lib/constants";

    export let steps = [];
    export let fact = {};
    export let location = "";

    const isContributor = queryStore({
        client: getContextClient(),
        query: gql`
            query getContributorStatus {
                isContributor {
                    id
                    username
                }
            }
        `,
    });
    let contributionArea = location?.pathname.split("/").pop();
    let signUp = `/fxa/authenticate?${new URLSearchParams({
        next: "/contribute/" + contributionArea,
        contributor: contributionArea,
    }).toString()}`;
</script>

<section class="mzp-l-content">
    <h2>{gettext("How you can contribute")}</h2>

    <div class="wrapper">
        <ol>
            <li>
                {#if !$isContributor.data?.isContributor?.id}
                    <Linkable link={signUp}>
                        {gettext("Sign up as a volunteer")}
                    </Linkable>
                {:else}
                    <Linkable link={TEACHABLE_URL}>
                        {gettext("Take the contributor's CPG training.")}
                    </Linkable>
                {/if}
            </li>
            {#each steps as [step, rest]}
                <li>
                    <svelte:component this={step} {...rest} />
                </li>
            {/each}
        </ol>
        <div class="fact">
            <span class="number">{fact.number}</span>
            <span class="text">{fact.text}</span>
        </div>
    </div>
</section>

<style lang="scss">
    @use "@mozilla-protocol/core/protocol/css/includes/lib" as p;

    h2 {
        text-align: center;
        margin: var(--spacing-lg) 0;
    }

    .wrapper {
        display: flex;
        flex-direction: column;

        @media #{p.$mq-lg} {
            flex-direction: row;
        }
    }

    ol,
    .fact {
        flex: 1;
    }

    ol {
        margin: 0;
        counter-reset: step;

        @media #{p.$mq-lg} {
            margin-right: var(--spacing-md);
        }
    }

    li {
        background: var(--tile-bg);
        box-shadow: var(--tile-shadow);
        border-radius: p.$border-radius-sm;

        font-family: var(--base-font-family);
        font-weight: 600;
        font-size: 20px;
        line-height: 24px;

        padding: var(--spacing-sm);
        margin-bottom: var(--spacing-md);

        display: flex;
        align-items: center;

        @media #{p.$mq-lg} {
            &:last-of-type {
                margin-bottom: 0;
            }
        }

        &::before {
            content: counter(step);
            counter-increment: step;

            width: 48px;
            height: 48px;
            margin-right: var(--spacing-sm);
            flex: none;

            background: var(--step-number-bg);
            border-radius: 52px;

            line-height: 48px;
            color: var(--step-number-color);

            text-align: center;
        }
    }

    .fact {
        background: var(--fact-bg);
        border-radius: p.$border-radius-sm;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: var(--spacing-md);
        font-family: var(--heading-font-family-moz);
        font-weight: bold;

        .number {
            color: var(--fact-number);
            font-size: 72px;
            line-height: 120%;
        }

        .text {
            color: var(--fact-color);
            font-style: italic;
            font-weight: 500;
            font-size: 36px;
            line-height: 120%;
            text-align: center;
        }
    }
</style>
