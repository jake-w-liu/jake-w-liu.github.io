// Has to be in the head tag, otherwise a flicker effect will occur.

// Toggle through light, dark, and system theme settings.
let toggleThemeSetting = () => {
  let themeSetting = determineThemeSetting();
  if (themeSetting == "system") {
    setThemeSetting("light");
  } else if (themeSetting == "light") {
    setThemeSetting("dark");
  } else {
    setThemeSetting("system");
  }
};

// Change the theme setting and apply the theme.
let setThemeSetting = (themeSetting) => {
  localStorage.setItem("theme", themeSetting);

  document.documentElement.setAttribute("data-theme-setting", themeSetting);

  applyTheme();
};

// Apply the computed dark or light theme to the website.
let applyTheme = () => {
  let theme = determineComputedTheme();

  transTheme();
  setHighlight(theme);
  setGiscusTheme(theme);
  setSearchTheme(theme);

  // if mermaid is not defined, do nothing
  if (typeof mermaid !== "undefined") {
    setMermaidTheme(theme);
  }

  // if diff2html is not defined, do nothing
  if (typeof Diff2HtmlUI !== "undefined") {
    setDiff2htmlTheme(theme);
  }

  // if echarts is not defined, do nothing
  if (typeof echarts !== "undefined") {
    setEchartsTheme(theme);
  }

  // if Plotly is not defined, do nothing
  if (typeof Plotly !== "undefined") {
    setPlotlyTheme(theme);
  }

  // if vegaEmbed is not defined, do nothing
  if (typeof vegaEmbed !== "undefined") {
    setVegaLiteTheme(theme);
  }

  document.documentElement.setAttribute("data-theme", theme);

  // Add class to tables.
  let tables = document.getElementsByTagName("table");
  for (let i = 0; i < tables.length; i++) {
    if (theme == "dark") {
      tables[i].classList.add("table-dark");
    } else {
      tables[i].classList.remove("table-dark");
    }
  }

  // Set jupyter notebooks themes.
  let jupyterNotebooks = document.getElementsByClassName("jupyter-notebook-iframe-container");
  for (let i = 0; i < jupyterNotebooks.length; i++) {
    let bodyElement = jupyterNotebooks[i].getElementsByTagName("iframe")[0].contentWindow.document.body;
    if (theme == "dark") {
      bodyElement.setAttribute("data-jp-theme-light", "false");
      bodyElement.setAttribute("data-jp-theme-name", "JupyterLab Dark");
    } else {
      bodyElement.setAttribute("data-jp-theme-light", "true");
      bodyElement.setAttribute("data-jp-theme-name", "JupyterLab Light");
    }
  }

  // Updates the background of medium-zoom overlay.
  if (typeof medium_zoom !== "undefined") {
    medium_zoom.update({
      background: getComputedStyle(document.documentElement).getPropertyValue("--global-bg-color") + "ee", // + 'ee' for trasparency.
    });
  }
};

let setHighlight = (theme) => {
  if (theme == "dark") {
    document.getElementById("highlight_theme_light").media = "none";
    document.getElementById("highlight_theme_dark").media = "";
  } else {
    document.getElementById("highlight_theme_dark").media = "none";
    document.getElementById("highlight_theme_light").media = "";
  }
};

let setGiscusTheme = (theme) => {
  function sendMessage(message) {
    const iframe = document.querySelector("iframe.giscus-frame");
    if (!iframe) return;
    iframe.contentWindow.postMessage({ giscus: message }, "https://giscus.app");
  }

  sendMessage({
    setConfig: {
      theme: theme,
    },
  });
};

let addMermaidZoom = (records, observer) => {
  var svgs = d3.selectAll(".mermaid svg");
  svgs.each(function () {
    var svg = d3.select(this);
    svg.html("<g>" + svg.html() + "</g>");
    var inner = svg.select("g");
    var zoom = d3.zoom().on("zoom", function (event) {
      inner.attr("transform", event.transform);
    });
    svg.call(zoom);
  });
  observer.disconnect();
};

let setMermaidTheme = (theme) => {
  if (theme == "light") {
    // light theme name in mermaid is 'default'
    // https://mermaid.js.org/config/theming.html#available-themes
    theme = "default";
  }

  /* Re-render the SVG, based on https://github.com/cotes2020/jekyll-theme-chirpy/blob/master/_includes/mermaid.html */
  document.querySelectorAll(".mermaid").forEach((elem) => {
    // Get the code block content from previous element, since it is the mermaid code itself as defined in Markdown, but it is hidden
    let svgCode = elem.previousSibling.childNodes[0].innerHTML;
    elem.removeAttribute("data-processed");
    elem.innerHTML = svgCode;
  });

  mermaid.initialize({ theme: theme });
  window.mermaid.init(undefined, document.querySelectorAll(".mermaid"));

  const observable = document.querySelector(".mermaid svg");
  if (observable !== null) {
    var observer = new MutationObserver(addMermaidZoom);
    const observerOptions = { childList: true };
    observer.observe(observable, observerOptions);
  }
};

let setDiff2htmlTheme = (theme) => {
  document.querySelectorAll(".diff2html").forEach((elem) => {
    // Get the code block content from previous element, since it is the diff code itself as defined in Markdown, but it is hidden
    let textData = elem.previousSibling.childNodes[0].innerHTML;
    elem.innerHTML = "";
    const configuration = { colorScheme: theme, drawFileList: true, highlight: true, matching: "lines" };
    const diff2htmlUi = new Diff2HtmlUI(elem, textData, configuration);
    diff2htmlUi.draw();
  });
};

let setEchartsTheme = (theme) => {
  document.querySelectorAll(".echarts").forEach((elem) => {
    // Get the code block content from previous element, since it is the echarts code itself as defined in Markdown, but it is hidden
    let jsonData = elem.previousSibling.childNodes[0].innerHTML;
    echarts.dispose(elem);

    if (theme === "dark") {
      var chart = echarts.init(elem, "dark-fresh-cut");
    } else {
      var chart = echarts.init(elem);
    }

    chart.setOption(JSON.parse(jsonData));
  });
};

let setPlotlyTheme = (theme) => {
  document.querySelectorAll(".js-plotly-plot").forEach((elem) => {
    // Get the code block content from previous element, since it is the plotly code itself as defined in Markdown, but it is hidden
    let jsonData = JSON.parse(elem.previousSibling.childNodes[0].innerHTML);

    if (theme === "dark") {
      // dark theme extracted from https://github.com/plotly/plotly.py/blob/main/plotly/package_data/templates/plotly_dark.json?raw=true
      // prettier-ignore
      const plotlyDarkLayout = {"layout":{"autotypenumbers":"strict","colorway":["#7B90D2","#F75C2F","#00AA90","#B28FCE","#FC9F4D","#2EA9DF","#E87A90","#B5CAA0","#F8C3CD","#F6C555"],"font":{"color":"#FCFAF2"},"hovermode":"closest","hoverlabel":{"align":"left"},"paper_bgcolor":"rgb(11, 16, 19)","plot_bgcolor":"rgb(11, 16, 19)","polar":{"bgcolor":"rgb(11, 16, 19)","angularaxis":{"gridcolor":"#566C73","linecolor":"#566C73","ticks":""},"radialaxis":{"gridcolor":"#566C73","linecolor":"#566C73","ticks":""}},"ternary":{"bgcolor":"rgb(11, 16, 19)","aaxis":{"gridcolor":"#566C73","linecolor":"#566C73","ticks":""},"baxis":{"gridcolor":"#566C73","linecolor":"#566C73","ticks":""},"caxis":{"gridcolor":"#566C73","linecolor":"#566C73","ticks":""}},"coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"sequential":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]],"sequentialminus":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]],"diverging":[[0,"#8E354A"],[0.1,"#C1328E"],[0.2,"#E87A90"],[0.3,"#F8C3CD"],[0.4,"#FEDFE1"],[0.5,"#FCFAF2"],[0.6,"#FEDFE1"],[0.7,"#B5CAA0"],[0.8,"#90B44B"],[0.9,"#516E41"],[1,"#42602D"]]},"xaxis":{"gridcolor":"#26453D","linecolor":"#566C73","ticks":"","title":{"standoff":15},"zerolinecolor":"#26453D","automargin":true,"zerolinewidth":2},"yaxis":{"gridcolor":"#26453D","linecolor":"#566C73","ticks":"","title":{"standoff":15},"zerolinecolor":"#26453D","automargin":true,"zerolinewidth":2},"scene":{"xaxis":{"backgroundcolor":"rgb(11, 16, 19)","gridcolor":"#566C73","linecolor":"#566C73","showbackground":true,"ticks":"","zerolinecolor":"#A5DEE4","gridwidth":2},"yaxis":{"backgroundcolor":"rgb(11, 16, 19)","gridcolor":"#566C73","linecolor":"#566C73","showbackground":true,"ticks":"","zerolinecolor":"#A5DEE4","gridwidth":2},"zaxis":{"backgroundcolor":"rgb(11, 16, 19)","gridcolor":"#566C73","linecolor":"#566C73","showbackground":true,"ticks":"","zerolinecolor":"#A5DEE4","gridwidth":2}},"shapedefaults":{"line":{"color":"#FCFAF2"}},"annotationdefaults":{"arrowcolor":"#FCFAF2","arrowhead":0,"arrowwidth":1},"geo":{"bgcolor":"rgb(11, 16, 19)","landcolor":"rgb(11, 16, 19)","subunitcolor":"#566C73","showland":true,"showlakes":true,"lakecolor":"rgb(11, 16, 19)"},"title":{"x":0.05},"updatemenudefaults":{"bgcolor":"#566C73","borderwidth":0},"sliderdefaults":{"bgcolor":"#A5DEE4","borderwidth":1,"bordercolor":"rgb(11, 16, 19)","tickwidth":0},"mapbox":{"style":"dark"}},"data":{"histogram2dcontour":[{"type":"histogram2dcontour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]]}],"choropleth":[{"type":"choropleth","colorbar":{"outlinewidth":0,"ticks":""}}],"histogram2d":[{"type":"histogram2d","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]]}],"heatmap":[{"type":"heatmap","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]]}],"contourcarpet":[{"type":"contourcarpet","colorbar":{"outlinewidth":0,"ticks":""}}],"contour":[{"type":"contour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]]}],"surface":[{"type":"surface","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]]}],"mesh3d":[{"type":"mesh3d","colorbar":{"outlinewidth":0,"ticks":""}}],"scatter":[{"marker":{"line":{"color":"#26453D"}},"type":"scatter"}],"parcoords":[{"type":"parcoords","line":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolargl":[{"type":"scatterpolargl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"bar":[{"error_x":{"color":"#FCFAF2"},"error_y":{"color":"#FCFAF2"},"marker":{"line":{"color":"rgb(11, 16, 19)","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"scattergeo":[{"type":"scattergeo","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolar":[{"type":"scatterpolar","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"scattergl":[{"marker":{"line":{"color":"#26453D"}},"type":"scattergl"}],"scatter3d":[{"type":"scatter3d","line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattermap":[{"type":"scattermap","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattermapbox":[{"type":"scattermapbox","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterternary":[{"type":"scatterternary","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattercarpet":[{"type":"scattercarpet","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"carpet":[{"aaxis":{"endlinecolor":"#BDC0BA","gridcolor":"#566C73","linecolor":"#566C73","minorgridcolor":"#566C73","startlinecolor":"#BDC0BA"},"baxis":{"endlinecolor":"#BDC0BA","gridcolor":"#566C73","linecolor":"#566C73","minorgridcolor":"#566C73","startlinecolor":"#BDC0BA"},"type":"carpet"}],"table":[{"cells":{"fill":{"color":"#566C73"},"line":{"color":"rgb(11, 16, 19)"}},"header":{"fill":{"color":"#255359"},"line":{"color":"rgb(11, 16, 19)"}},"type":"table"}],"barpolar":[{"marker":{"line":{"color":"rgb(11, 16, 19)","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"pie":[{"automargin":true,"type":"pie"}]}};

      // if jsonData.layout exists, then update the theme
      if (jsonData.layout) {
        if (jsonData.layout.template) {
          jsonData.layout.template = { ...plotlyDarkLayout, ...jsonData.layout.template };
        } else {
          jsonData.layout.template = plotlyDarkLayout;
        }
      } else {
        jsonData.layout = { template: plotlyDarkLayout };
      }
    } else {
      // light theme extracted from https://github.com/plotly/plotly.py/blob/main/plotly/package_data/templates/plotly_white.json?raw=true
      // prettier-ignore
      const plotlyLightLayout = {"layout":{"autotypenumbers":"strict","colorway":["#7B90D2","#F75C2F","#00AA90","#B28FCE","#FC9F4D","#2EA9DF","#E87A90","#B5CAA0","#F8C3CD","#F6C555"],"font":{"color":"#255359"},"hovermode":"closest","hoverlabel":{"align":"left"},"paper_bgcolor":"#FFFFFB","plot_bgcolor":"#FFFFFB","polar":{"bgcolor":"#FFFFFB","angularaxis":{"gridcolor":"#FCFAF2","linecolor":"#FCFAF2","ticks":""},"radialaxis":{"gridcolor":"#FCFAF2","linecolor":"#FCFAF2","ticks":""}},"ternary":{"bgcolor":"#FFFFFB","aaxis":{"gridcolor":"#FCFAF2","linecolor":"#BDC0BA","ticks":""},"baxis":{"gridcolor":"#FCFAF2","linecolor":"#BDC0BA","ticks":""},"caxis":{"gridcolor":"#FCFAF2","linecolor":"#BDC0BA","ticks":""}},"coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"sequential":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]],"sequentialminus":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]],"diverging":[[0,"#8E354A"],[0.1,"#C1328E"],[0.2,"#E87A90"],[0.3,"#F8C3CD"],[0.4,"#FEDFE1"],[0.5,"#FCFAF2"],[0.6,"#FEDFE1"],[0.7,"#B5CAA0"],[0.8,"#90B44B"],[0.9,"#516E41"],[1,"#42602D"]]},"xaxis":{"gridcolor":"#FCFAF2","linecolor":"#FCFAF2","ticks":"","title":{"standoff":15},"zerolinecolor":"#FCFAF2","automargin":true,"zerolinewidth":2},"yaxis":{"gridcolor":"#FCFAF2","linecolor":"#FCFAF2","ticks":"","title":{"standoff":15},"zerolinecolor":"#FCFAF2","automargin":true,"zerolinewidth":2},"scene":{"xaxis":{"backgroundcolor":"#FFFFFB","gridcolor":"#FCFAF2","linecolor":"#FCFAF2","showbackground":true,"ticks":"","zerolinecolor":"#FCFAF2","gridwidth":2},"yaxis":{"backgroundcolor":"#FFFFFB","gridcolor":"#FCFAF2","linecolor":"#FCFAF2","showbackground":true,"ticks":"","zerolinecolor":"#FCFAF2","gridwidth":2},"zaxis":{"backgroundcolor":"#FFFFFB","gridcolor":"#FCFAF2","linecolor":"#FCFAF2","showbackground":true,"ticks":"","zerolinecolor":"#FCFAF2","gridwidth":2}},"shapedefaults":{"line":{"color":"#255359"}},"annotationdefaults":{"arrowcolor":"#255359","arrowhead":0,"arrowwidth":1},"geo":{"bgcolor":"#FFFFFB","landcolor":"#FFFFFB","subunitcolor":"#A5DEE4","showland":true,"showlakes":true,"lakecolor":"#FFFFFB"},"title":{"x":0.05},"mapbox":{"style":"light"}},"data":{"histogram2dcontour":[{"type":"histogram2dcontour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]]}],"choropleth":[{"type":"choropleth","colorbar":{"outlinewidth":0,"ticks":""}}],"histogram2d":[{"type":"histogram2d","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]]}],"heatmap":[{"type":"heatmap","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]]}],"contourcarpet":[{"type":"contourcarpet","colorbar":{"outlinewidth":0,"ticks":""}}],"contour":[{"type":"contour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]]}],"surface":[{"type":"surface","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#113285"],[0.1111111111111111,"#66327C"],[0.2222222222222222,"#6F3381"],[0.3333333333333333,"#C1328E"],[0.4444444444444444,"#C1328E"],[0.5555555555555556,"#D05A6E"],[0.6666666666666666,"#ED784A"],[0.7777777777777778,"#FC9F4D"],[0.8888888888888888,"#EFBB24"],[1.0,"#DDD23B"]]}],"mesh3d":[{"type":"mesh3d","colorbar":{"outlinewidth":0,"ticks":""}}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"parcoords":[{"type":"parcoords","line":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolargl":[{"type":"scatterpolargl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"bar":[{"error_x":{"color":"#255359"},"error_y":{"color":"#255359"},"marker":{"line":{"color":"#FFFFFB","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"scattergeo":[{"type":"scattergeo","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolar":[{"type":"scatterpolar","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"scattergl":[{"type":"scattergl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatter3d":[{"type":"scatter3d","line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattermap":[{"type":"scattermap","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattermapbox":[{"type":"scattermapbox","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterternary":[{"type":"scatterternary","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattercarpet":[{"type":"scattercarpet","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"carpet":[{"aaxis":{"endlinecolor":"#255359","gridcolor":"#A5DEE4","linecolor":"#A5DEE4","minorgridcolor":"#A5DEE4","startlinecolor":"#255359"},"baxis":{"endlinecolor":"#255359","gridcolor":"#A5DEE4","linecolor":"#A5DEE4","minorgridcolor":"#A5DEE4","startlinecolor":"#255359"},"type":"carpet"}],"table":[{"cells":{"fill":{"color":"#FCFAF2"},"line":{"color":"#FFFFFB"}},"header":{"fill":{"color":"#A5DEE4"},"line":{"color":"#FFFFFB"}},"type":"table"}],"barpolar":[{"marker":{"line":{"color":"#FFFFFB","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"pie":[{"automargin":true,"type":"pie"}]}};

      // if jsonData.layout exists, then update the theme
      if (jsonData.layout) {
        if (jsonData.layout.template) {
          jsonData.layout.template = { ...plotlyLightLayout, ...jsonData.layout.template };
        } else {
          jsonData.layout.template = plotlyLightLayout;
        }
      } else {
        jsonData.layout = { template: plotlyLightLayout };
      }
    }

    Plotly.relayout(elem, jsonData.layout);
  });
};

let setVegaLiteTheme = (theme) => {
  document.querySelectorAll(".vega-lite").forEach((elem) => {
    // Get the code block content from previous element, since it is the vega lite code itself as defined in Markdown, but it is hidden
    let jsonData = elem.previousSibling.childNodes[0].innerHTML;
    elem.innerHTML = "";
    if (theme === "dark") {
      vegaEmbed(elem, JSON.parse(jsonData), { theme: "dark" });
    } else {
      vegaEmbed(elem, JSON.parse(jsonData));
    }
  });
};

let setSearchTheme = (theme) => {
  const ninjaKeys = document.querySelector("ninja-keys");
  if (!ninjaKeys) return;

  if (theme === "dark") {
    ninjaKeys.classList.add("dark");
  } else {
    ninjaKeys.classList.remove("dark");
  }
};

let transTheme = () => {
  document.documentElement.classList.add("transition");
  window.setTimeout(() => {
    document.documentElement.classList.remove("transition");
  }, 500);
};

// Determine the expected state of the theme toggle, which can be "dark", "light", or
// "system". Default is "system".
let determineThemeSetting = () => {
  let themeSetting = localStorage.getItem("theme");
  if (themeSetting != "dark" && themeSetting != "light" && themeSetting != "system") {
    themeSetting = "system";
  }
  return themeSetting;
};

// Determine the computed theme, which can be "dark" or "light". If the theme setting is
// "system", the computed theme is determined based on the user's system preference.
let determineComputedTheme = () => {
  let themeSetting = determineThemeSetting();
  if (themeSetting == "system") {
    const userPref = window.matchMedia;
    if (userPref && userPref("(prefers-color-scheme: dark)").matches) {
      return "dark";
    } else {
      return "light";
    }
  } else {
    return themeSetting;
  }
};

let initTheme = () => {
  let themeSetting = determineThemeSetting();

  setThemeSetting(themeSetting);

  // Add event listener to the theme toggle button.
  document.addEventListener("DOMContentLoaded", function () {
    const mode_toggle = document.getElementById("light-toggle");

    mode_toggle.addEventListener("click", function () {
      toggleThemeSetting();
    });
  });

  // Add event listener to the system theme preference change.
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", ({ matches }) => {
    applyTheme();
  });
};
