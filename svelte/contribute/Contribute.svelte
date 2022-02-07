<script>
    import { Router, Route } from "svelte-navigator";
    import Picker from "./Picker";

    export let locale = "";
</script>

<svelte:head>
    <title>{gettext("Contribute")} | {gettext("Mozilla Support")}</title>
</svelte:head>

<div class="sumo-page-section--inner">
    <h1>{gettext("Contribute Page Scaffolding")}</h1>

    <Router basepath="/{locale}/contribute">
        <Route path="forum">
            <p>{gettext("This is the forum contribution area")}</p>
            <Picker />
        </Route>
        <Route path="kb">
            <p>{gettext("This is the support article contribution area")}</p>
            <Picker />
        </Route>
        <Route path="social">
            <p>{gettext("This is the social support contribution area")}</p>
            <Picker />
        </Route>
        <Route path="/">
            <p>{gettext("This is the landing page")}</p>
            <Picker />
        </Route>
    </Router>
</div>
