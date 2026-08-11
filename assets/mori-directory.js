(() => {
  "use strict";

  const input = document.querySelector("#directory-search");
  const clearButton = document.querySelector("#search-clear");
  const cards = Array.from(document.querySelectorAll("[data-directory-card]"));
  const filters = Array.from(document.querySelectorAll("[data-category-filter]"));
  const count = document.querySelector("#result-count");
  const empty = document.querySelector("#no-results");
  if (!input || !cards.length || !count || !empty) return;

  let activeCategory = "all";
  const normalize = (value) => value.normalize("NFKC").toLocaleLowerCase("ja-JP").replace(/\s+/g, " ").trim();

  const apply = () => {
    const terms = normalize(input.value).split(" ").filter(Boolean);
    let visible = 0;
    cards.forEach((card) => {
      const haystack = normalize(card.dataset.search || card.textContent || "");
      const categories = (card.dataset.categories || "").split("｜");
      const categoryMatches = activeCategory === "all" || categories.includes(activeCategory);
      const searchMatches = terms.every((term) => haystack.includes(term));
      card.hidden = !(categoryMatches && searchMatches);
      if (!card.hidden) visible += 1;
    });
    count.textContent = `${visible}件を表示`;
    empty.hidden = visible !== 0;
  };

  input.addEventListener("input", apply);
  clearButton?.addEventListener("click", () => {
    input.value = "";
    input.focus();
    apply();
  });
  filters.forEach((button) => {
    button.addEventListener("click", () => {
      activeCategory = button.dataset.categoryFilter || "all";
      filters.forEach((item) => {
        const selected = item === button;
        item.classList.toggle("is-active", selected);
        item.setAttribute("aria-pressed", String(selected));
      });
      apply();
    });
  });
})();
