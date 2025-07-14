import datasets from "$data/datasets.csv";
import { timeParse, timeFormat } from "d3-time-format";

const strToArray = (str) => str.split(",").map((d) => d.trim());

const parseDate = timeParse("%m/%d/%Y");
const formatMonth = timeFormat("%b %Y");

const clean = datasets
  .map((d) => ({
    ...d,
    date: parseDate(d.date),
    month: formatMonth(parseDate(d.date)),
    keywords: strToArray(d.keywords),
    filters: strToArray(d.filters),
  }))
  .filter((d) => !d.hide_all);

export default clean;