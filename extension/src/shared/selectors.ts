export const POST_SELECTORS = [
  "div[role='listitem'][componentkey^='update-card-focus']",
  "div.feed-shared-update-v2[data-urn]",
  "div[data-urn^='urn:li:activity']",
  "li[data-urn^='urn:li:activity']",
];

export const AUTHOR_NAME_SELECTORS = [
  ".update-components-actor__name span[aria-hidden='true']",
  ".update-components-actor__name",
  "a.update-components-actor__meta-link span[aria-hidden='true']",
];

export const AUTHOR_LINK_SELECTORS = [
  "a[href*='/in/']",
  "a.update-components-actor__meta-link[href]",
];

export const HEADLINE_SELECTORS = [
  ".update-components-actor__description",
  ".update-components-actor__sub-description",
];

export const TEXT_SELECTORS = [
  ".update-components-text",
  ".feed-shared-text",
  "[data-testid='expandable-text-box']",
];

export const REACTION_SELECTORS = [
  "button[aria-label^='Reaction button state:']",
  ".social-details-social-counts__reactions-count",
  "button[aria-label*='reaction']",
];

export const COMMENT_COUNT_SELECTORS = [
  "button[aria-label='Comment']",
  "button[aria-label*='comment']",
  ".social-details-social-counts__comments",
];

export const REPOST_SELECTORS = [
  "button[aria-label='Repost']",
  "button[aria-label*='repost']",
  ".social-details-social-counts__reposts",
];

export const PERMALINK_SELECTORS = [
  "a[href*='/feed/update/']",
  "a[href*='urn:li:activity']",
];

export const COMMENT_ITEM_SELECTORS = [
  ".comments-comment-item",
  ".comments-comment-entity",
];

export const COMMENT_AUTHOR_SELECTORS = [
  ".comments-post-meta__name",
  ".comments-comment-meta__description-title",
  "a[href*='/in/']",
];

export const COMMENT_TEXT_SELECTORS = [
  ".comments-comment-item__main-content",
  ".comments-comment-entity__content",
  ".comments-comment-item-content-body",
];
