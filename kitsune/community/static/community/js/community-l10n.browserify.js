/* jshint esnext: true */
import CommunityController from "./CommunityController.js";
import { UserChip, RelativeTime } from "./contributors-common.jsx";

var controller = new CommunityController({
  area: "l10n",
  target: document.querySelector("#main-content"),
  title: "Top Contributors - Knowledge Base",
  columns: [
    { key: "rank", title: "Rank" },
    { key: "user", title: "Name", transform: (u) => <UserChip {...u} /> },
    { key: "revision_count", title: "Revisions" },
    { key: "review_count", title: "Reviews" },
    {
      key: "last_contribution_date",
      title: "Last Activity",
      transform: (timestamp) => (
        <RelativeTime timestamp={timestamp} future={false} />
      ),
    },
  ],
});
controller.render();

window.onpopstate = function () {
  controller.refresh();
};
