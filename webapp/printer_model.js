class PrinterModel {
  constructor(printer_info) {
    // copy template
    const template = document.querySelector("#printer_visualizer_template").content;
    this.node = template.cloneNode(true);
    this.div = this.node.querySelector(".printer_visualizer");
    this.div.id = printer_info["printer_name"];
    document.body.append(this.node);

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
    this.div.querySelector(".printer_name").innerHTML = this.printer_info["printer_name"];
    this.div.querySelector(".printjob_name").innerHTML = this.printer_info["printjob_name"];
    this.div.querySelector(".printer_state").innerHTML = this.printer_info["printer_state"];
    this.div.querySelector(".printjob_state").innerHTML = this.printer_info["printjob_state"];
    this.div.querySelector(".result").innerHTML = this.printer_info["result"];

    this.div.querySelector(".input_img").src = this.printer_info["input_img_path"];
    this.div.querySelector(".sim_img").src = this.printer_info["sim_img_path"];
    this.div.querySelector(".predict_img").src = this.printer_info["predict_img_path"];
  }

  expired() {
    console.log(this.printer_info + " lost connection");
  }
}
