class PrinterModel {
  constructor(printer_info) {
    // copy template
    const template = document.querySelector("#printer_visualizer_template").content;
    this.node = template.cloneNode(true);
    this.div = this.node.querySelector(".printer_visualizer");
    this.div.id = printer_info["printer_name"];
    document.getElementById("printer_list").appendChild(this.node);

    // setup model
    this.printer_info = {};
    this.update(printer_info);
  }

  update(printer_info) {
    this.dirty = false;
    for (var key in printer_info) {
      if (!key in this.printer_info || this.printer_info[key] !== printer_info[key]) {
        this.dirty = true;
        break;
      }
    }
    this.printer_info = printer_info;

    // update view
    if (this.dirty) {
      this.updateView();
    }

    this.isExpired = false;
  }

  updateView() {
    this.div.querySelector(".printer_name").innerHTML = "UM" + this.printer_info["printer_name"];

    // printjob name
    var printjob_text = this.div.querySelector(".printjob_name");
    if (this.printer_info["printjob_name"] != null) {
      if (this.printer_info["printer_state"] == "printing") {
        printjob_text.innerHTML = "Print Job: " + this.printer_info["printjob_name"];
      } else {
        printjob_text.innerHTML = "Last Print Job: " + this.printer_info["printjob_name"];
      }
      printjob_text.style.display = "";
    } else {
      printjob_text.style.display = "none";
    }

    // printer state
    var ps_span = this.div.querySelector(".printer_state");
    ps_span.innerHTML = this.printer_info["printer_state"];
    ps_span.className = "printer_state badge ";
    switch (this.printer_info["printer_state"]) {
      case "printing":
        ps_span.className += "bg-primary";
        break;
      default:
        // idle
        ps_span.className += "bg-secondary";
    }

    // printjob state
    var pj_span = this.div.querySelector(".printjob_state");
    if (this.printer_info["printer_state"] === "printing" && this.printer_info["printjob_state"] != null) {
      pj_span.style.display = "";
      pj_span.innerHTML = this.printer_info["printjob_state"];
      pj_span.className = "printjob_state badge ";
      switch (this.printer_info["printjob_state"]) {
        case "printing":
          pj_span.className += "bg-primary";
          break;
        case "wait_cleanup":
          pj_span.className += "bg-warning";
          break;
        default:
          // preprint, post_print
          pj_span.className += "bg-secondary";
      }
    } else {
      pj_span.style.display = "none";
    }

    // result
    var result_com = this.div.querySelector(".evaluation");
    var iou_bar = this.div.querySelector(".iou");
    if (this.printer_info["result"] != null) {
      var result = this.printer_info["result"].split(",");
      var loss = parseFloat(result[0]);
      var iou = parseFloat(result[2]).toFixed(2);
      // console.log("Loss:", loss, ", IOU:", iou);
      iou_bar.innerHTML = "Smoothed IOU: " + iou;
      iou_bar.setAttribute("aria-valuenow", iou);
      iou_bar.style.width = iou * 100 + "%";
      // change color
      iou_bar.className = "iou progress-bar progress-bar-striped progress-bar-animated ";
      if (iou > 0.6) {
        iou_bar.className += "bg-success";
      } else if (iou > 0.3) {
        iou_bar.className += "bg-warning";
      } else {
        iou_bar.className += "bg-danger";
      }
      result_com.style.display = "";
    } else {
      result_com.style.display = "none";
    }

    // images
    this.updateImage("input_img");
    this.updateImage("sim_img");
    this.updateImage("predict_img");
    this.updateImage("iou_img");
    this.updateImage("blend_img");
  }

  updateImage(img_name) {
    var img_com = this.div.querySelector("." + img_name);
    if (this.printer_info[img_name + "_path"] != null) {
      img_com.src = this.printer_info[img_name + "_path"];
      img_com.style.display = "";
    } else {
      img_com.style.display = "none";
    }
  }

  expired() {
    console.log(this.printer_info + " lost connection");
  }
}
