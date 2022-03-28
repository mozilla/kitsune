<script>
    import Header from "./Header";
    import Picker from "./Picker";
    import aboutImg from "./img/About Us.png";

    export let img;
</script>

<svelte:head>
    <title>{gettext("Contribute")} | {gettext("Mozilla Support")}</title>
</svelte:head>

<Header {img}>
    <h1>{gettext("Save the world from the comfort of your couch")}</h1>

    <p>
        {gettext(
            "Help millions of users get the most out of their favorite browser. Your contributions will reach millions of users worldwide, and you can do it from the comfort of your couch!"
        )}
    </p>

    <h2>{gettext("We need your help!")}</h2>

    <p>
        {gettext(
            "Used by more than 400 million people, Mozilla support is fully powered by volunteers, and it’s more important than ever. This is where you come in."
        )}
    </p>
</Header>

<Picker />

<section class="mzp-l-content hero">
    <div class="text">
        <h2>{gettext("About us")}</h2>
        <p>
            {gettext(
                "Mozilla Support is a community of enthusiastic volunteers and employees trying to support our users around the globe. Join us for an incredible adventure!"
            )}
        </p>
    </div>
    <img
        src={aboutImg}
        alt={gettext("Photo of Mozilla staff and volunteers.")}
    />
</section>

<style lang="scss">
    @use "@mozilla-protocol/core/protocol/css/includes/lib" as p;

    .hero {
        display: flex;
        flex-direction: column-reverse;
        align-items: center;
        margin-bottom: var(--spacing-lg);

        @media #{p.$mq-lg} {
            flex-direction: row-reverse;
        }

        img,
        .text {
            flex: 1;
        }

        .text {
            margin-top: 24px;

            @media #{p.$mq-lg} {
                margin-top: 0;
            }
        }
    }
</style>
