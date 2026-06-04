import React from "react";

export default function QueryBox({ onSubmit, disabled }) {
  const [value, setValue] = React.useState("");

  function handleSubmit(e) {
    e.preventDefault();
    const q = value.trim();
    if (!q) return;
    onSubmit(q);
    setValue("");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <textarea
        style={styles.textarea}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask Śaṅkarācārya... (Sanskrit, English, or Kannada)"
        disabled={disabled}
        rows={2}
      />
      <button style={{ ...styles.button, opacity: disabled || !value.trim() ? 0.5 : 1 }} type="submit" disabled={disabled || !value.trim()}>
        ➤
      </button>
    </form>
  );
}

const styles = {
  form: {
    display: "flex",
    gap: "0.5rem",
    alignItems: "flex-end",
  },
  textarea: {
    flex: 1,
    background: "rgba(232,213,163,0.07)",
    border: "1px solid rgba(232,213,163,0.2)",
    borderRadius: 8,
    color: "#e8d5a3",
    padding: "0.75rem 1rem",
    fontSize: "1rem",
    fontFamily: "inherit",
    resize: "none",
    outline: "none",
    lineHeight: 1.5,
  },
  button: {
    background: "#b89b6a",
    color: "#0e0c09",
    border: "none",
    borderRadius: 8,
    width: 44,
    height: 44,
    fontSize: "1.1rem",
    cursor: "pointer",
    flexShrink: 0,
  },
};
