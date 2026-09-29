1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
100
101
102
103
104
105
106
107
108
109
110
111
112
import { useEffect, useRef, useState } from "react";

import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import SessionTimer from "./components/SessionTimer";
import { useChatSession } from "./hooks/useChatSession";

import "./App.css";
import "./assets/ai-study.css";
import aiStudyAvatar from "./assets/ai-study-avatar.png";

function TutorApp({ onCompleted }) {
  const {
    messages,
    phase,
    isWaiting,
    isComplete,
    sendMessage,
    resetSession,
    startSession,
  } = useChatSession();

  const hasStarted = useRef(false);
  const completionHandled = useRef(false);
  const [transitionError, setTransitionError] = useState("");


  const sessionTime = "20:00";
  useEffect(() => {
    if (hasStarted.current) {
      return;
    }

    hasStarted.current = true;
    startSession();
  }, []);

  useEffect(() => {
    if (!isComplete || !onCompleted || completionHandled.current) {
      return;
    }

    completionHandled.current = true;
    onCompleted().catch((error) => {
      console.error("Unable to load post-test:", error);
      setTransitionError("The conversation is complete, but the post-test could not be loaded.");
    });
  }, [isComplete, onCompleted]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="tutor-brand">
          <img
            src={aiStudyAvatar}
            alt=""
            className="tutor-brand__avatar"
          />

          <div className="tutor-brand__text">
            <h1 className="tutor-brand__name">AI Study</h1>
            <span className="tutor-brand__status">
              Ready
            </span>
          </div>
        </div>

        <button
        className="new-session-button"
        onClick={resetSession}
        >
        New session
        </button>

      </header>

      <SessionTimer
        sessionTime={sessionTime}
        visible={true}
        phase={phase}
        isComplete={isComplete}
      />

      <ChatWindow messages={messages}
      isWaiting={isWaiting}
      />

      {transitionError && (
        <div role="alert">
          <p>{transitionError}</p>
          <button type="button" onClick={() => {
            setTransitionError("");
            onCompleted().catch((error) => {
              console.error("Unable to load post-test:", error);
              setTransitionError("The post-test could not be loaded. Please try again.");
            });
          }}>
            Continue to post-test
          </button>
        </div>
      )}

      <ChatInput
        onSend={sendMessage}
        disabled={isWaiting || isComplete}
      />
    </div>
  );
}

export default TutorApp;
