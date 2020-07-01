/* jshint esnext: true */
import CommunityController from "./CommunityController.js";
import { UserChip, RelativeTime } from "./contributors-common.jsx";

var controller = new CommunityController({
  area: "questions",
  target: document.querySelector("#main-content"),
  title: "Top Contributors - Questions",
  columns: [
    { key: "rank", title: "Rank" },
    { key: "user", title: "Name", transform: (u) => <UserChip {...u} /> },
    { key: "answer_count", title: "Answers" },
    { key: "solution_count", title: "Solutions" },
    { key: "helpful_vote_count", title: "Helpful Votes" },
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
