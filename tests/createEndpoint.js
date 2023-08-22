
import { check } from 'k6';
import http from 'k6/http';

export default function () {

    let data = {
        "oid": "64e452b7a5d3a9d4ed79bb8d",
        "external_id": "28",
        "tags": [
            "nulla magna mollit",
            "consequat nulla in sit"
        ],
        "websockets": [
            "ut ea",
            "anim eu dolor",
            "adipisicing labore",
            "minim laboris cupidatat Ut"
        ],
        "emails": [
            "i.iwxvy@qq.com",
            "s.zbhippb@qq.com",
            "j.vtujsdlot@qq.com",
            "i.qdknavv@qq.com"
        ],
        "global_id": "64e452b7a5d3a9d4ed79bb8d"
    }

    const res = http.post('http://localhost:8000/endpoints', JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
