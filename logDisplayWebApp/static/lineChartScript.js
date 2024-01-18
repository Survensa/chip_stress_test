let width = 800;
let height = 500;
const margin = { top: 20, right: 20, bottom: 50, left: 40 };
let zoom_value = 10
let zoom_refactor_val = 10
var dataElement = document.getElementById('data');
const summary_json = JSON.parse(dataElement.textContent || dataElement.innerText);
pairing_data = summary_json["analytics"]['pairing_duration_info']
let keys = Object.keys(pairing_data)
let values = Object.values(pairing_data)
const data = []
for (i=0;i<keys.length;i++){
    data.push({x:keys[i],y:values[i]})
}

document.getElementById("zoom-refactor").value = zoom_refactor_val
const x = d3.scaleLinear()
    .domain([0, summary_json["number_of_iterations"]])
    .range([margin.left, width - margin.right]);

const y = d3.scaleLinear()
    .domain([0, Math.max(...values)+10])
    .range([height - margin.bottom, margin.top]);

const line = d3.line()
    .x(d => x(d.x))
    .y(d => y(d.y));

const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height);

svg.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0,${height - margin.bottom})`)
    .style("font","bold")
    .call(d3.axisBottom(x));

svg.append("g")
    .attr("class", "y-axis")
    .attr("transform", `translate(${margin.left},0)`)
    .call(d3.axisLeft(y));

svg.append("path")
    .datum(data)
    .attr("class", "line")
    .attr("fill", "none")
    .attr("stroke", "steelblue")
    .attr("stroke-width", 2)
    .attr("d", line);
svg.selectAll(".plot-point")  // Correct class selector
    .data(data)
    .enter()
    .append("circle")
    .attr("class", "plot-point")  // Assign a class to the circles
    .attr("fill", "red")
    .attr("stroke", "none")
    .attr("cx", function (d) { return x(d.x) })
    .attr("cy", function (d) { return y(d.y) })
    .attr("r", 4)
    .on("mouseover", handleMouseOver)
    .on("mouseout", handleMouseOut);

// Add zoom functionality
let zoom = d3.zoom()
    .scaleExtent([1, 10])
    .on("zoom", zoomed);

svg.call(zoom);
let tooltip = d3.select("#container").append("div")
    .attr("class", "tooltip")
    .style("opacity", 0)
    .style("background-color", "white")
    .style("border", "solid")
    .style("border-width", "2px")
    .style("border-radius", "5px")
    .style("padding", "5px")
    .style("position","absolute");
function zoomed(event) {
    const newXScale = event.transform.rescaleX(x);
    svg.select(".x-axis").call(d3.axisBottom(newXScale));
    svg.select(".line").attr("d", line.x(d => newXScale(d.x)));
    updateZoomLevel(event.transform.k);
    // Ensure that the y-axis is not affected by zoom
    y.range([height - margin.bottom, margin.top]);
    svg.select(".y-axis").call(d3.axisLeft(y));

    svg.selectAll(".plot-point")
        .attr("cx", d => newXScale(d.x))
        .attr("cy", d => y(d.y));
}

function updateZoomLevel(zoomLevel) {

    document.getElementById("zoomLevel").textContent = `Zoom Level: ${zoomLevel.toFixed(2)}`;
}

function zoom_func() {
    // svg.transition().call(zoom.scaleExtent,50)
    svg.transition().call(zoom.scaleBy, document.getElementById("zoom-input").value);
}
function zoom_refactor() {
    zoom.scaleExtent([1, Number(document.getElementById("zoom-refactor").value)])
}
function increaseHeight() {
    height += Number(document.getElementById("incr-height").value);
    svg.attr("height", height);
    y.range([height - margin.bottom, margin.top]);
    svg.select(".y-axis").call(d3.axisLeft(y));
    svg.select(".line").attr("d", line);
    svg.select(".x-axis")
        .attr("transform", `translate(0,${height - margin.bottom})`);

    svg.select(".line").attr("d", line);

    svg.selectAll(".plot-point")
        .attr("cy", d => y(d.y));

}

function decreaseHeight() {
    height -= Number(document.getElementById("decr-height").value);
    svg.attr("height", height);
    y.range([height - margin.bottom, margin.top]);
    svg.select(".y-axis").call(d3.axisLeft(y));
    svg.select(".line").attr("d", line);
    svg.select(".x-axis")
        .attr("transform", `translate(0,${height - margin.bottom})`);

    svg.select(".line").attr("d", line);

    svg.selectAll(".plot-point")
        .attr("cy", d => y(d.y));
}

function increaseWidth() {
    width += Number(document.getElementById("incr-width").value);
    svg.attr("width", width);
    x.range([margin.left, width - margin.right]);
    svg.select(".x-axis").call(d3.axisBottom(x));
    svg.select(".line").attr("d", line);

    svg.selectAll(".plot-point")
        .attr("cx", d => x(d.x));

}

function decreaseWidth() {
    width -= Number(document.getElementById("decr-width").value)
    svg.attr("width", width);
    x.range([margin.left, width - margin.right]);
    svg.select(".x-axis").call(d3.axisBottom(x));
    svg.select(".line").attr("d", line);

    svg.selectAll(".plot-point")
        .attr("cx", d => x(d.x));

}

function handleMouseOver(event, d) {
    console.log("mouse")
    tooltip.transition()
        .duration(200)
        .style("opacity", .9);
    tooltip
        .html(`Iteration Number: ${d.x}<br>Pairing Duration: ${d.y}`)
        .style("top", (event.pageY-100)+"px")
        .style("left",(event.pageX-100)+"px");

}

function handleMouseOut() {

    tooltip.transition()
        .duration(500)
        .style("opacity", 0);
}

document.getElementById("container").appendChild(svg.node());


