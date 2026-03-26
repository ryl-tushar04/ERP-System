import { useEffect, useMemo, useRef } from "react";
import cytoscape from "cytoscape";

function shortenLabel(label, maxLength = 42) {
  if (!label) {
    return "";
  }

  if (label.length <= maxLength) {
    return label;
  }

  return `${label.slice(0, maxLength - 3)}...`;
}

function buildGraphElements(graph) {
  return [
    ...graph.nodes.map((node) => ({
      data: {
        id: node.id,
        label: shortenLabel(node.label),
        type: node.type,
      },
    })),
    ...graph.edges.map((edge) => ({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label || edge.type,
        type: edge.type,
      },
    })),
  ];
}

function nodeColor(type) {
  const palette = {
    customer: "#155eef",
    address: "#7a5af8",
    order: "#0f766e",
    delivery: "#ea580c",
    invoice: "#b42318",
    payment: "#047857",
    product: "#3659a6",
  };

  return palette[type] || "#475467";
}

export default function QueryGraph({ graph }) {
  const containerRef = useRef(null);
  const elements = useMemo(() => buildGraphElements(graph), [graph]);
  const hasGraph = graph.nodes.length > 0;

  useEffect(() => {
    if (!containerRef.current || !hasGraph) {
      return undefined;
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      layout: {
        name: graph.nodes.length > 12 ? "grid" : "cose",
        padding: 28,
        animate: false,
        fit: true,
        nodeRepulsion: 11000,
        idealEdgeLength: 140,
        edgeElasticity: 70,
      },
      style: [
        {
          selector: "node",
          style: {
            "background-color": (ele) => nodeColor(ele.data("type")),
            color: "#ffffff",
            label: "data(label)",
            "font-size": 11,
            "font-weight": 700,
            "text-wrap": "wrap",
            "text-max-width": 120,
            "text-valign": "center",
            "text-halign": "center",
            width: 96,
            height: 96,
            "border-width": 3,
            "border-color": "#ffffff",
          },
        },
        {
          selector: "edge",
          style: {
            width: 2,
            "line-color": "#c6d3ea",
            "target-arrow-color": "#c6d3ea",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            label: "data(label)",
            "font-size": 9,
            color: "#52607a",
            "text-background-color": "#ffffff",
            "text-background-opacity": 1,
            "text-background-padding": 2,
          },
        },
      ],
    });

    return () => cy.destroy();
  }, [elements, graph.nodes.length, hasGraph]);

  if (!hasGraph) {
    return (
      <div style={styles.emptyState}>
        Graph data will appear here once the seeded ERP graph or query subgraph is loaded.
      </div>
    );
  }

  return <div ref={containerRef} style={styles.graph} />;
}

const styles = {
  graph: {
    width: "100%",
    height: "620px",
    borderRadius: "16px",
    border: "1px solid #d9e2ef",
    background: "#f8fbff",
  },
  emptyState: {
    minHeight: "220px",
    display: "grid",
    placeItems: "center",
    borderRadius: "16px",
    border: "1px dashed #c6d3ea",
    background: "#f8fbff",
    color: "#66748d",
    padding: "24px",
    textAlign: "center",
  },
};
