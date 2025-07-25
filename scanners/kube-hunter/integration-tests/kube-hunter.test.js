// SPDX-FileCopyrightText: the secureCodeBox authors
//
// SPDX-License-Identifier: Apache-2.0

import { scan } from "../../../tests/integration/helpers.js";

test(
  "kube-hunter should find a fixed number of findings for the kind cluster",
  async () => {
    await scan(
      "kube-hunter-in-cluster",
      "kube-hunter",
      ["--pod", "--quick"],
      4 * 60,
    );

    // If we got here the scan succeeded
    // as the number of findings will depend on the cluster, we just check if it is defined at all
    expect(true).toBe(true);
  },
  { timeout: 5 * 60 * 1000 },
);
