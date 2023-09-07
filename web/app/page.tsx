'use client'

import { useEffect, useRef, useState } from "react"

import {
  Card,
  CardBody,
  CardFooter,
  Typography,
  Button,
  CardHeader,
  Input,
  Chip,
  Tabs,
  TabsHeader,
  Tab,
  Avatar,
  IconButton,
  Tooltip,
} from "@material-tailwind/react";

function StaticReportCard(props: { title: string, desc: string, static: number }) {
  return (
    <Card variant="gradient" color="blue-gray" shadow={true}>
      <CardBody>
        <Typography variant="h6" color="white">
          {props.title}
        </Typography>
        <Typography variant="h2" color="white">{props.static}</Typography>
      </CardBody>
    </Card>
  );
}
import {
  ChevronUpDownIcon,
} from "@heroicons/react/24/outline";
import { UserGroupIcon, EnvelopeIcon, Square3Stack3DIcon } from "@heroicons/react/24/solid";


function SortableTable(props: { title: string, desc: string, headers: Array<string>, rows: Array<any> }) {
  return (
    <Card className="h-full w-full">
      <CardHeader floated={false} shadow={false} className="rounded-none">
        <div className="mb-8 flex items-center justify-between gap-8">
          <div>
            <Typography variant="h5" color="blue-gray">
              {props.title}
            </Typography>
            <Typography color="gray" className="mt-1 font-normal">
              {props.desc}
            </Typography>
          </div>
          <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
            <Button variant="outlined" size="sm">
              查看所有
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardBody className="overflow-scroll px-0">
        <table className="mt-4 w-full min-w-max table-auto text-left">
          <thead>
            <tr>
              {props.headers.map((head, index) => (
                <th
                  key={head}
                  className="cursor-pointer border-y border-blue-gray-100 bg-blue-gray-50/50 p-4 transition-colors hover:bg-blue-gray-50"
                >
                  <Typography
                    variant="small"
                    color="blue-gray"
                    className="flex items-center justify-between gap-2 font-normal leading-none opacity-70"
                  >
                    {head}{" "}
                    {index !== props.headers.length - 1 && (
                      <ChevronUpDownIcon strokeWidth={2} className="h-4 w-4" />
                    )}
                  </Typography>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {
              props.rows.map((row, index) => (
                <tr key={props.title + index}>
                  {
                    Object.keys(row).map((k: string, i: number) => (
                      <td key={k + i} className="p-4 border-b border-blue-gray-50">
                        <Typography variant="small" color="blue-gray" className="font-normal">{row[k]}</Typography>
                      </td>
                    ))
                  }
                </tr>
              ))
            }
          </tbody>
        </table>
      </CardBody>
      <CardFooter className="flex items-center justify-between border-t border-blue-gray-50 p-4">
        <Typography variant="small" color="blue-gray" className="font-normal">
          Page 1 of 10
        </Typography>
        <div className="flex gap-2">
          <Button variant="outlined" size="sm">
            上一页
          </Button>
          <Button variant="outlined" size="sm">
            下一页
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}

import React from "react";
import {
  TabsBody,
  TabPanel,
} from "@material-tailwind/react";


function TabsWithIcon() {
  const data = [
    {
      label: "消息列表",
      value: "message_list",
      icon: EnvelopeIcon,
      desc: `所有消息, 包含所有单独发送的消息和计划执行产生的消息`,
      headers: ["消息ID", "渠道类型", "发送状态", "接收人", "发送时间"],
      rows: [
        ["123456", "WEBSOCKET", "已发送", "lingfromsh@163.com", "2023-08-23 10:11:57"],
        ["123456", "WEBSOCKET", "已发送", "lingfromsh@163.com", "2023-08-23 10:11:57"],
        ["123456", "WEBSOCKET", "已发送", "lingfromsh@163.com", "2023-08-23 10:11:57"],
        ["123456", "WEBSOCKET", "已发送", "lingfromsh@163.com", "2023-08-23 10:11:57"],
        ["123456", "WEBSOCKET", "已发送", "lingfromsh@163.com", "2023-08-23 10:11:57"],
        ["123456", "WEBSOCKET", "已发送", "lingfromsh@163.com", "2023-08-23 10:11:57"],
      ]
    },
    {
      label: "终端列表",
      value: "endpoint_list",
      icon: UserGroupIcon,
      desc: `所有用户终端, 包含用户自己的渠道通信方式`,
      headers: ["终端ID", "ExternalID", "渠道数", "创建时间"],
      rows: []
    },
    {
      label: "计划列表",
      value: "plan_list",
      icon: Square3Stack3DIcon,
      desc: `所有消息计划, 包含长期循环执行、单次消息计划`,
      headers: ["计划ID", "是否生效", "计划类型", "创建时间"],
      rows: []
    },
  ];
  return (
    <Tabs value="message_list" >
      <TabsHeader>
        {data.map(({ label, value, icon }) => (
          <Tab key={value} value={value}>
            <div className="flex items-center gap-2">
              {React.createElement(icon, { className: "w-5 h-5" })}
              {label}
            </div>
          </Tab>
        ))}
      </TabsHeader>
      <TabsBody>
        {data.map(({ label, value, desc, headers, rows }) => (
          <TabPanel key={value} value={value}>
            <SortableTable title={label} desc={desc} headers={headers} rows={rows} />
          </TabPanel>
        ))}
      </TabsBody>
    </Tabs>
  );
}
const initWebsocket = () => {
  const ws = new WebSocket("ws://localhost:8000/metrics");

  return ws
}


export default function Page() {

  const $websocket: any = useRef(null);

  useEffect(() => {
    if ($websocket.current == null) {
      $websocket.current = initWebsocket();
      $websocket.current.addEventListener("message", ({ data }) => {
        let packet = JSON.parse(data);
        console.log(packet);
        setTotalMsgCount(packet.total_count_of_messages);
        setTodayMsgCount(packet.today_count_of_messages);
        setTotalEndpointCount(packet.total_count_of_endpoints);
        setCurrentSendSpeed(packet.speed_of_messages);
        setTotalPlanCount(packet.total_count_of_plans);
        setTodayPlanExecutionCount(packet.today_count_of_plan_executions);
      });
    }

  });
  const [totalEndpointCount, setTotalEndpointCount] = useState(0);
  const [totalMsgCount, setTotalMsgCount] = useState(0);
  const [todayMsgCount, setTodayMsgCount] = useState(0);
  const [currentSendSpeed, setCurrentSendSpeed] = useState(0);
  const [totalPlanCount, setTotalPlanCount] = useState(0);
  const [todayPlanExecutionCount, setTodayPlanExecutionCount] = useState(0);

  return <div className="container mx-auto">
    <div className="columns-3 py-1 mt-1">
      <StaticReportCard title="总发送消息数量(条):" static={totalMsgCount} desc="jji" />
      <StaticReportCard title="今日发送消息数量(条):" static={todayMsgCount} desc="jji" />
      <StaticReportCard title="当前发送速率数量(条):" static={currentSendSpeed} desc="jji" />
    </div>
    <div className="columns-3 py-1">
      <StaticReportCard title="总计划数量(条):" static={totalPlanCount} desc="jji" />
      <StaticReportCard title="今日执行计划数量(条):" static={todayPlanExecutionCount} desc="jji" />
      <StaticReportCard title="总终端数量(条):" static={totalEndpointCount} desc="jji" />
    </div>
    <TabsWithIcon />
    <div className="absolute bottom-20 right-20 z-auto visible">
      <IconButton size="lg" variant="outlined" className="rounded-full">
        <i className="fa-solid fa-circle-plus"></i>
      </IconButton>
    </div>
  </div >
}