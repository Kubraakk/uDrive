//
//  DetailsViewController.swift
//  uDrive
//
//  Created by Kübra AKPUNAR on 23.05.2024.
//

import UIKit

class DetailsViewController: UIViewController {

    @IBOutlet weak var titleLabel: UILabel!
    @IBOutlet weak var analysisImage: UIImageView!
    @IBOutlet weak var infoLabel: UILabel!
    var selectedDriveData = ""
    override func viewDidLoad() {
        super.viewDidLoad()
        titleLabel.text = selectedDriveData


    }
    

}
