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
    var result_com = this.div.querySelector(".result");
    if (this.printer_info["result"] != null) {
      var result = this.printer_info["result"].split(",");
      var loss = parseFloat(result[0]);
      var iou = parseFloat(result[1]);
      // console.log("Loss:", loss, ", IOU:", iou);
      result_com.innerHTML = "Loss: " + loss + ", IOU: " + iou;
      result_com.style.display = "";
    } else {
      result_com.style.display = "none";
    }

    // images
    var input_img = this.div.querySelector(".input_img");
    if (this.printer_info["input_img_path"] != null) {
      input_img.src = this.printer_info["input_img_path"];
      input_img.style.display = "";
    } else {
      input_img.style.display = "none";
    }
    var sim_img = this.div.querySelector(".sim_img");
    if (this.printer_info["sim_img_path"] != null) {
      sim_img.src = this.printer_info["sim_img_path"];
      sim_img.style.display = "";
    } else {
      sim_img.style.display = "none";
    }
    var predict_img = this.div.querySelector(".predict_img");
    if (this.printer_info["predict_img_path"] != null) {
      predict_img.src = this.printer_info["predict_img_path"];
      predict_img.style.display = "";
    } else {
      predict_img.style.display = "none";
    }
    var iou_img = this.div.querySelector(".iou_img");
    if (this.printer_info["iou_img_path"] != null) {
      iou_img.src = this.printer_info["iou_img_path"];
      iou_img.style.display = "";
    } else {
      iou_img.style.display = "none";
    }
  }

  expired() {
    console.log(this.printer_info + " lost connection");
  }
}
