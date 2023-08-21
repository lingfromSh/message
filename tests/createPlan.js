
import { check } from 'k6';
import http from 'k6/http';

export default function () {

    let data = { "query": "mutation createPlan {\n    createPlan(\n        input: {\n            name: \"每1分钟发送一次消息\"\n            triggers: [\n                {\n                    type: REPEAT\n                    repeatAt: \"0-59/1 * * * *\"\n                    repeatTime: -1\n                    startTime: \"2023-08-02T00:39:59+08:00\"\n                }\n            ]\n            subPlans: [\n                {\n                    provider: \"64e362199f351203b2e42a0c\"\n                    message: {\n                        connections: [\"#exid:studio:1\"]\n                        action: \"say.hello\"\n                        payload: \"hello\"\n                    }\n                }\n            ]\n            isEnabled: true\n        }\n    ){\n        isEnabled\n    }\n}\n" }

    const res = http.post('http://localhost:8000/graphql', JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
