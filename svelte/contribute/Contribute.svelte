<script>
    import { Router, Route } from "svelte-navigator";
    import Area from "./Area";
    import Landing from "./Landing";

    // this is a little verbose, but dynamic imports aren't SSRed
    // if we do this in more places, we could write a webpack loader
    import imgScreensPng from "./img/Screens.png";
    import imgScreensWebp from "./img/Screens.webp";
    import imgScreens2xWebp from "./img/Screens@2x.webp";
    import imgHeadsPng from "./img/Heads.png";
    import imgHeadsWebp from "./img/Heads.webp";
    import imgHeads2xWebp from "./img/Heads@2x.webp";
    import imgIntroductionPng from "./img/Introduction.png";
    import imgIntroductionWebp from "./img/Introduction.webp";
    import imgIntroduction2xWebp from "./img/Introduction@2x.webp";
    import imgFoundationPng from "./img/Foundation.png";
    import imgFoundationWebp from "./img/Foundation.webp";
    import imgFoundation2xWebp from "./img/Foundation@2x.webp";
    import imgDotsPng from "./img/Dots.png";
    import imgDotsWebp from "./img/Dots.webp";
    import imgDots2xWebp from "./img/Dots@2x.webp";
    import imgHandsPng from "./img/Hands.png";
    import imgHandsWebp from "./img/Hands.webp";
    import imgHands2xWebp from "./img/Hands@2x.webp";

    export let url = "";
    export let locale = "";
</script>

<Router basepath="/{locale}/contribute" {url}>
    <Route path="forum" let:location>
        <Area
            area={gettext("Support forum")}
            images={[imgHeadsPng, imgHeadsWebp, imgHeads2xWebp]}
            {location}
            steps={{
                steps: [
                    gettext("Find support questions"),
                    gettext("Start answering!"),
                    gettext("Learn more about forum contribution"),
                ],
                fact: {
                    number: gettext("1 → 1000"),
                    text: gettext(
                        "Solving one issue helps up to 1000 users a day"
                    ),
                },
            }}
        >
            <h1>{gettext("Answer questions in the support forum")}</h1>
            <h2>{gettext("Where all the action happens")}</h2>
            <p>
                {gettext(`From hardcore web developers to "how do I install Firefox"
                    first time users, everybody needs your help in the forum!
                    Share your knowledge by pointing people to the right help
                    articles and providing troubleshooting steps for their
                    individual questions.`)}
            </p>
        </Area>
    </Route>
    <Route path="kb" let:location>
        <Area
            area={gettext("Support articles")}
            images={[
                imgIntroductionPng,
                imgIntroductionWebp,
                imgIntroduction2xWebp,
            ]}
            {location}
            steps={{
                steps: [
                    gettext("Explore the Knowledge Base Dashboard"),
                    gettext(
                        "Check the Needs Update column and start editing articles!"
                    ),
                    gettext("Learn more about Knowledge Base contribution"),
                ],
                fact: {
                    number: gettext("400 → 70+"),
                    text: gettext(
                        "One article can be viewed by 400 million users and translated into 70+ languages"
                    ),
                },
            }}
        >
            <h1>{gettext("Help us write help articles")}</h1>
            <h2>{gettext("Share your wisdom with the world!")}</h2>
            <p>
                {gettext(
                    "If you like writing and teaching then the Knowledge Base is the place for you. We need contributors that can write, edit or proofread articles in English. Thousands of people are accessing our Knowledge Base every week. Imagine how many will be helped by you!"
                )}
            </p>
        </Area>
    </Route>
    <Route path="l10n" let:location>
        <Area
            area={gettext("Localization")}
            images={[imgFoundationPng, imgFoundationWebp, imgFoundation2xWebp]}
            {location}
            steps={{
                steps: [
                    gettext(
                        "Check if your locale is available and go to your localization dashboard"
                    ),
                    gettext("Start localizing an article!"),
                    gettext("Learn more about localization contribution"),
                ],
                fact: {
                    number: gettext("400 → 70+"),
                    text: gettext(
                        "One article can be viewed by 400 million users and translated into 70+ languages"
                    ),
                },
            }}
        >
            <h1>{gettext("Translate help articles")}</h1>
            <h2>
                {gettext("Let’s make Mozilla Support speak your language!")}
            </h2>
            <p>
                {gettext(
                    "Help articles are not available in your language yet? You want to join the amazing team translating them? You will help millions of users in your language. Pretty heroic, right?"
                )}
            </p>
        </Area>
    </Route>
    <Route path="social" let:location>
        <Area
            area={gettext("Social support")}
            images={[imgDotsPng, imgDotsWebp, imgDots2xWebp]}
            {location}
            steps={{
                steps: [
                    gettext("Request access to Conversocial"),
                    gettext("Start tweeting from @FirefoxSupport!"),
                    gettext("Learn more about social support contribution"),
                ],
                fact: {
                    number: gettext("1 → 300+"),
                    text: gettext(
                        "Help 300+ users who reach out for support on Twitter every month"
                    ),
                },
            }}
        >
            <h1>{gettext("Support users on social media")}</h1>
            <h2>
                {gettext("Let’s help people so they can keep using Firefox!")}
            </h2>
            <p>
                {gettext(
                    "Many users ask support questions on social media. With social support, you can help them by reply to their questions from our official account, @FirefoxSupport. Pretty cool, right?"
                )}
            </p>
        </Area>
    </Route>
    <Route path="play-store" let:location>
        <Area
            area={gettext("Play Store support")}
            images={[imgHandsPng, imgHandsWebp, imgHands2xWebp]}
            {location}
            steps={{
                steps: [
                    gettext("Request access to Conversocial"),
                    gettext(
                        "Start replying to Play Store reviews for Firefox for Android!"
                    ),
                    gettext("Learn more about Play Store contribution"),
                ],
                fact: {
                    number: gettext("1 → 20k+"),
                    text: gettext(
                        "Help 20K+ users who leave reviews in Play Store every month"
                    ),
                },
            }}
        >
            <h1>{gettext("Support Firefox users on mobile")}</h1>
            <h2>
                {gettext(
                    "Help us respond to Play Store reviews for Firefox for Android!"
                )}
            </h2>
            <p>
                {gettext(
                    "Smartphones are taking over the world. We have many users leaving reviews while also asking for support on Play Store. By joining Play Store Support, you can help them by reply to their reviews from the comfort of your desk. Pretty simple, right?"
                )}
            </p>
        </Area>
    </Route>
    <Route path="/">
        <Landing images={[imgScreensPng, imgScreensWebp, imgScreens2xWebp]} />
    </Route>
</Router>

<style lang="scss">
    @use "@mozilla-protocol/core/protocol/css/includes/lib" as p;
    @use "../../kitsune/sumo/static/sumo/scss/config/typography-mixins";

    :global(#svelte) {
        --color: var(--color-dark-gray-10);
        --header-bg: var(--color-shade-bg);
        --tile-bg: var(--page-bg);
        --tile-shadow: 0px 2px 6px rgba(58, 57, 68, 0.2);
        --step-number-bg: #{p.$color-pink-50};
        --step-number-color: var(--color-white);
        --fact-bg: #241541;
        --fact-number: #{p.$color-pink-50};
        --fact-color: var(--color-white);
        --spacing-sm: 16px;
        --spacing-md: 32px;
        --spacing-lg: 64px;

        color: var(--color);
    }

    :global(h1) {
        @include typography-mixins.text-display-xl(moz);
    }

    :global(h2) {
        @include typography-mixins.text-display-sm(moz);
    }

    :global(p) {
        @include typography-mixins.text-body-md;
    }
</style>
