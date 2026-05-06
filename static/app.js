document.addEventListener("DOMContentLoaded", () => {
  const questionForm = document.getElementById("question-form");
  const questionInput = document.getElementById("question-input");
  const questionSubmitButton = document.querySelector(".question-submit-button");
  const exampleChips = document.querySelectorAll(".example-chip");
  const loadingPanel = document.getElementById("loading-panel");
  const loadingQuestion = document.getElementById("loading-question");
  const loadingMessage = document.getElementById("loading-message");
  const stagedMessages = [
    "Searching approved IT documentation...",
    "Finding the most relevant support guide...",
    "Preparing troubleshooting steps...",
  ];
  let loadingMessageIndex = 0;
  let loadingMessageTimer = null;

  const autoSizeInput = (expanded = false) => {
    if (!questionInput) {
      return;
    }
    questionInput.style.height = "52px";
    const nextHeight = Math.max(questionInput.scrollHeight, expanded ? 104 : 52);
    questionInput.style.height = `${nextHeight}px`;
  };

  const startLoadingMessages = () => {
    if (!loadingMessage) {
      return;
    }
    loadingMessage.textContent = stagedMessages[0];
    if (loadingMessageTimer !== null) {
      window.clearInterval(loadingMessageTimer);
    }
    loadingMessageIndex = 0;
    loadingMessageTimer = window.setInterval(() => {
      loadingMessageIndex = (loadingMessageIndex + 1) % stagedMessages.length;
      loadingMessage.textContent = stagedMessages[loadingMessageIndex];
    }, 900);
  };

  const showLoadingPanel = () => {
    if (!loadingPanel) {
      return;
    }
    const currentQuestion = questionInput ? questionInput.value.trim() : "";
    loadingQuestion.textContent = currentQuestion
      ? `You asked: “${currentQuestion}”`
      : "Searching for the best approved support guide.";
    loadingPanel.hidden = false;
    startLoadingMessages();
    loadingPanel.scrollIntoView({ behavior: "auto", block: "start" });
  };

  const setLoadingState = () => {
    if (questionSubmitButton) {
      questionSubmitButton.disabled = true;
      questionSubmitButton.classList.add("is-loading");
      questionSubmitButton.textContent = "Getting help...";
    }
    if (questionInput) {
      questionInput.setAttribute("aria-busy", "true");
    }
    showLoadingPanel();
  };

  const submitQuestionForm = () => {
    if (!questionForm) {
      return;
    }
    setLoadingState();
    questionForm.submit();
  };

  if (questionInput && questionForm) {
    autoSizeInput();

    questionInput.addEventListener("focus", () => {
      autoSizeInput(true);
    });

    questionInput.addEventListener("input", () => {
      autoSizeInput(questionInput === document.activeElement || questionInput.value.trim().length > 0);
    });

    questionInput.addEventListener("blur", () => {
      autoSizeInput(questionInput.value.trim().length > 0);
    });

    questionInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        submitQuestionForm();
      }
    });
  }

  if (questionForm) {
    questionForm.addEventListener("submit", () => {
      setLoadingState();
    });
  }

  for (const chip of exampleChips) {
    chip.addEventListener("click", () => {
      if (questionInput) {
        questionInput.value = chip.dataset.question;
        autoSizeInput(true);
      }
      submitQuestionForm();
    });
  }

  const responseCard = document.getElementById("response");
  if (responseCard && responseCard.dataset.hasResponse === "1") {
    responseCard.scrollIntoView({ behavior: "auto", block: "start" });
  }
});
