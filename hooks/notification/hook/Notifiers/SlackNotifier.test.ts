// SPDX-FileCopyrightText: the secureCodeBox authors
//
// SPDX-License-Identifier: Apache-2.0

import { SlackNotifier } from "./SlackNotifier";
import { NotificationChannel } from "../model/NotificationChannel";
import { NotifierType } from "../NotifierType";
import { Scan } from "../model/Scan";

const originalFetch = global.fetch;

beforeEach(() => {
  global.fetch = jest.fn().mockImplementation(() =>
    Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ ok: true })
    })
  );
});

afterEach(() => {
  global.fetch = originalFetch;
});

const channel: NotificationChannel = {
  name: "Channel Name",
  type: NotifierType.SLACK,
  template: "slack-messageCard",
  rules: [],
  endPoint: "https://hooks.slack.com/services/<YOUR_TOKEN>",
};

test("Should Send Message With Findings And Severities", async () => {
  const scan: Scan = {
    metadata: {
      uid: "09988cdf-1fc7-4f85-95ee-1b1d65dbc7cc",
      name: "demo-scan-1601086432",
      namespace: "my-scans",
      creationTimestamp: new Date("2021-01-01T14:29:25Z"),
      labels: {
        company: "iteratec",
        "attack-surface": "external",
      },
    },
    spec: {
      scanType: "Nmap",
      parameters: ["-Pn", "localhost"],
    },
    status: {
      findingDownloadLink:
        "https://s3.securecodebox.example.com/scan-b9as-sdweref--sadf-asdfsdf-dasdgf-asdffdsfa7/findings.json",
      findings: {
        categories: {
          "A Client Error response code was returned by the server": 1,
          "Information Disclosure - Sensitive Information in URL": 1,
          "Strict-Transport-Security Header Not Set": 1,
        },
        count: 3,
        severities: {
          high: 10,
          medium: 5,
          low: 2,
          informational: 1,
        },
      },
      finishedAt: new Date("2020-05-25T02:38:13Z"),
      rawResultDownloadLink:
        "https://s3.securecodebox.example.com/scan-blkfsdg-sdgfsfgd-sfg-sdfg-dfsg-gfs98-e8af2172caa7/zap-results.json?Expires=1601691232",
      rawResultFile: "zap-results.json",
      rawResultType: "zap-json",
      state: "Done",
    },
  };

  const slackNotifier = new SlackNotifier(channel, scan, [], []);
  await slackNotifier.sendMessage();
  expect(global.fetch).toHaveBeenCalled();
});

test("Should Send Minimal Template For Empty Findings", async () => {
  const scan: Scan = {
    metadata: {
      uid: "09988cdf-1fc7-4f85-95ee-1b1d65dbc7cc",
      name: "demo-scan-1601086432",
      namespace: "my-scans",
      creationTimestamp: new Date("2021-01-01T14:29:25Z"),
      labels: {
        company: "iteratec",
        "attack-surface": "external",
      },
    },
    spec: {
      scanType: "Nmap",
      parameters: ["-Pn", "localhost"],
    },
    status: {
      findingDownloadLink:
        "https://s3.securecodebox.example.com/scan-b9as-sdweref--sadf-asdfsdf-dasdgf-asdffdsfa7/findings.json",
      findings: {},
      finishedAt: new Date("2020-05-25T02:38:13Z"),
      rawResultDownloadLink:
        "https://s3.securecodebox.example.com/scan-blkfsdg-sdgfsfgd-sfg-sdfg-dfsg-gfs98-e8af2172caa7/zap-results.json?Expires=1601691232",
      rawResultFile: "zap-results.json",
      rawResultType: "zap-json",
      state: "Done",
    },
  };

  const n = new SlackNotifier(channel, scan, [], []);
  await n.sendMessage();
  expect(global.fetch).toHaveBeenCalled();
});
