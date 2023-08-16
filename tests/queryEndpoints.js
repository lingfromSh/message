import { check } from 'k6';
import http from 'k6/http';

export default function () {

    let data = { "query": "query endpoints {\n    endpoints {\n      pageInfo {\n        hasNextPage\n        hasPreviousPage\n        currentPage\n        currentPageSize\n        totalPageCount\n        totalItemCount\n      }\n      edges {\n          id\n          oid\n          externalId\n          tags\n          websockets\n          emails\n      }\n    }\n}", "variables": {} }

    const res = http.post('http://localhost:8080/graphql', JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
