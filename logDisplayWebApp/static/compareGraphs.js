const margin = { top: 20, right: 20, bottom: 50, left: 40 };
let zoom_value = 10
let zoom_refactor_val = 10
var json_data
var svg_objects={}
async function printSelectedItems() {
    const divElements = document.querySelectorAll('.graph_styling');

// Loop through the div elements and clear their contents
divElements.forEach((div) => {
  div.replaceChildren();
});
    var selectedItems = [];
    // Loop through all checkboxes and check if they are selected
    $('.dropdown-item input[type="checkbox"]').each(function() {
        if ($(this).prop('checked')) {
            let selected_data=JSON.parse($(this).val())
            let selected_parameter=$(this).next("label").text().toLowerCase()
            selected_data["analytics"]=selected_parameter
            selectedItems.push(selected_data);
        }
    });
    let request_data=JSON.stringify({"fetch_data":selectedItems})
    let request_config={
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: request_data
      }
    let response = await fetch("/compareGraphData",request_config)
    if (response.status==200){
        json_data=await response.json()
        let json_data_array=json_data["fetch_data"]
        json_data_array.forEach(analytics_data => {
                let svg_node=svg_node_builder(analytics_data["summary_json"],analytics_data["analytics"])
                let div_element=document.createElement("div");
                let heading =document.createElement("p")
                let graph_name = analytics_data["script_name"]+" "+ analytics_data["iteration"] +" "+analytics_data["analytics"].toUpperCase()
                let display_name=analytics_data["script_name"]+" |--| "+ analytics_data["iteration"] +" |--| "+analytics_data["analytics"].toUpperCase()
                heading.textContent=display_name
                div_element.classList.add("graph_styling")
                div_element.appendChild(svg_node.svg.node())
                document.getElementById("container").appendChild(div_element);
                svg_objects[graph_name]=svg_node
                div_element.appendChild(heading)
                let select_tag=document.getElementById("analytics_options")
                var opt=document.createElement("option")
                opt.value=graph_name
                opt.innerHTML = graph_name;
                opt.setAttribute("id",graph_name)
                select_tag.appendChild(opt)
            })
        }
}

function svg_node_builder(summary_json,analytics_parameter){
        var width = 800;
        var height = 500;
        let analytics_parameter_data = summary_json["analytics"][analytics_parameter]
        console.log("summary_json")
        console.log(summary_json)
        console.log("analytics")
        console.log(summary_json["analytics"][analytics_parameter])
        let keys = Object.keys(analytics_parameter_data)
        let values = Object.values(analytics_parameter_data)
        const data = []
        for (i=0;i<keys.length;i++){
            data.push({x:keys[i],y:values[i]})
        }
        let x = d3.scaleLinear()
        .domain([0, summary_json["number_of_iterations"]])
        .range([margin.left, width - margin.right]);
    
        let y = d3.scaleLinear()
            .domain([0, Math.max(...values)+10])
            .range([height - margin.bottom, margin.top]);
    
        let line = d3.line()
            .x(d => x(d.x))
            .y(d => y(d.y));
    
        let svg = d3.create("svg")
            .attr("width", width)
            .attr("height", height);
        // Add zoom functionality
        let zoom = d3.zoom()
            .scaleExtent([1, 10])
            .on("zoom", zoomed);
        
        let tooltip = d3.select("#container").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0)
            .style("background-color", "white")
            .style("border", "solid")
            .style("border-width", "2px")
            .style("border-radius", "5px")
            .style("padding", "5px")
            .style("position","absolute");
    
        svg.append("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0,${height - margin.bottom})`)
            .style("font","bold")
            .style("overflow","auto")
            .call(d3.axisBottom(x));
    
        svg.append("g")
            .attr("class", "y-axis")
            .style("overflow","auto")
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
    
        svg.call(zoom);
        
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
        document.getElementById("zoom-refactor").value = zoom_refactor_val //this corresponds to html input element for taking zoom factor from user
        return {"svg":svg,"x":x,"y":y,"zoom":zoom,"line":line,"width":width,"height":height}
    }
function zoom_refactor() {
        let analytic_parameter_option = document.querySelector('#analytics_options').value;
        let svg_obj=svg_objects[analytic_parameter_option]
        let zoom=svg_obj["zoom"]
        zoom.scaleExtent([1, Number(document.getElementById("zoom-refactor").value)])
    }
    
function increaseHeight() {
        let analytic_parameter_option = document.querySelector('#analytics_options').value;
        let svg_obj=svg_objects[analytic_parameter_option]
        let svg=svg_obj.svg
        let x = d3.scaleLinear()
        .domain([0, summary_json["number_of_iterations"]])
        .range([margin.left, svg_obj.width - margin.right]);
        let line=svg_obj.line
        let y = svg_obj.y
        let zoom=svg_obj.zoom
        svg_obj.height += Number(document.getElementById("incr-height").value);
        // console.log(svg_obj.height)
        svg.attr("height",svg_obj.height );
        y.range([svg_obj.height - margin.bottom, margin.top]);
        svg.select(".y-axis").call(d3.axisLeft(y));
        svg.selectAll(".line").attr("d", svg_obj.line);
        svg.selectAll(".x-axis")
            .attr("transform", `translate(0,${svg_obj.height - margin.bottom})`);
        svg.select(".line").attr("d", svg_obj.line);
        svg.selectAll(".plot-point")
            .attr("cy", d => y(d.y));
        function zoomed(event) {
                const newXScale = event.transform.rescaleX(x);
                svg.select(".x-axis").call(d3.axisBottom(newXScale));
                svg.select(".line").attr("d", line.x(d => newXScale(d.x)));
                updateZoomLevel(event.transform.k);
                // Ensure that the y-axis is not affected by zoom
                y.range([svg_obj.height - margin.bottom, margin.top]);
                svg.select(".y-axis").call(d3.axisLeft(y));
        
                svg.selectAll(".plot-point")
                    .attr("cx", d => newXScale(d.x))
                    .attr("cy", d => y(d.y));
            }
            function updateZoomLevel(zoomLevel) {
    
                document.getElementById("zoomLevel").textContent = `Zoom Level: ${zoomLevel.toFixed(2)}`;
            }
        zoom.on("zoom",zoomed)
    
    }
    
function decreaseHeight() {
        let analytic_parameter_option = document.querySelector('#analytics_options').value;
        let svg_obj=svg_objects[analytic_parameter_option]
        let svg=svg_obj.svg
        let x = d3.scaleLinear()
        .domain([0, summary_json["number_of_iterations"]])
        .range([margin.left, svg_obj.width - margin.right]);
        let line=svg_obj.line
        let y = svg_obj.y
        let zoom=svg_obj.zoom
        svg_obj.height -= Number(document.getElementById("incr-height").value);
        // console.log(svg_obj.height)
        svg.attr("height",svg_obj.height );
        y.range([svg_obj.height - margin.bottom, margin.top]);
        svg.select(".y-axis").call(d3.axisLeft(y));
        svg.selectAll(".line").attr("d", svg_obj.line);
        svg.selectAll(".x-axis")
            .attr("transform", `translate(0,${svg_obj.height - margin.bottom})`);
        svg.select(".line").attr("d", svg_obj.line);
        svg.selectAll(".plot-point")
            .attr("cy", d => y(d.y));
        function zoomed(event) {
                const newXScale = event.transform.rescaleX(x);
                svg.select(".x-axis").call(d3.axisBottom(newXScale));
                svg.select(".line").attr("d", line.x(d => newXScale(d.x)));
                updateZoomLevel(event.transform.k);
                // Ensure that the y-axis is not affected by zoom
                y.range([svg_obj.height - margin.bottom, margin.top]);
                svg.select(".y-axis").call(d3.axisLeft(y));
        
                svg.selectAll(".plot-point")
                    .attr("cx", d => newXScale(d.x))
                    .attr("cy", d => y(d.y));
            }
            function updateZoomLevel(zoomLevel) {
    
                document.getElementById("zoomLevel").textContent = `Zoom Level: ${zoomLevel.toFixed(2)}`;
            }
        zoom.on("zoom",zoomed)
    }
    
function increaseWidth() {
        let analytic_parameter_option = document.querySelector('#analytics_options').value;
        let svg_obj=svg_objects[analytic_parameter_option]
        let svg=svg_obj.svg
        let x = svg_obj.x;
        let width = svg_obj.width
        width += Number(document.getElementById("incr-width").value);
        svg.attr("width", width);
        x.range([margin.left, width - margin.right]);
        svg.selectAll(".x-axis").call(d3.axisBottom(x));
        svg.selectAll(".line").attr("d", svg_obj.line);
        svg.selectAll(".plot-point")
            .attr("cx", d => x(d.x));
        
    
    }
    
function decreaseWidth() {
        let analytic_parameter_option = document.querySelector('#analytics_options').value;
        let svg_obj=svg_objects[analytic_parameter_option]
        let svg=svg_obj.svg
        let x=svg_obj.x
        let width = svg_obj.width
        width -= Number(document.getElementById("decr-width").value)
        svg.attr("width", width);
        x.range([margin.left, width - margin.right]);
        svg.selectAll(".x-axis").call(d3.axisBottom(x));
        svg.selectAll(".plot-point")
            .attr("cx", d => x(d.x));
        svg.selectAll(".line").attr("d", svg_obj.line);
    
    }
$(document).ready(function(){
    // Handle submenu toggle
    $('.dropdown-submenu a').on("click", function(e){
        $(this).next('ul').toggle();
        e.stopPropagation();
        e.preventDefault();
    });

    // Handle checkbox click
    $('.dropdown-item input[type="checkbox"]').on("click", function(e){
        e.stopPropagation();

        // If the clicked item has no nested levels, close the dropdown
        if (!$(this).parent().hasClass('dropdown-submenu')) {
            $('.dropdown').removeClass('show');
        }
    });

    // Close the dropdown when clicking outside
    $(document).on("click", function (e) {
        if (!$(e.target).closest('.dropdown').length) {
            $('.dropdown').removeClass('show');
        }
    });
});