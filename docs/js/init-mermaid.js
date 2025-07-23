window.addEventListener("load", () => {
  mermaid.initialize({
    startOnLoad: true,
    theme: "default",
    themeVariables: {
    fontSize: "10px",
    nodePadding: "20",
  },
    securityLevel: "loose"
  });
});
