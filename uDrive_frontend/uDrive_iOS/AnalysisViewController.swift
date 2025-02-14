//
//  AnalysisViewController.swift
//  uDrive
//
//  Created by Kübra AKPUNAR on 16.05.2024.
//

import UIKit

class AnalysisViewController: UIViewController, UITableViewDelegate,UITableViewDataSource {

    @IBOutlet weak var tableView: UITableView!
    var driveData = [String]()
    var chosenDriveData = ""
    
    override func viewDidLoad() {
        super.viewDidLoad()
        //delegasyon ve datasource yetkisini tableViewa self ile veriyoruz.
        tableView.delegate = self
        tableView.dataSource = self
        
        driveData.append("Genel Sürüş Analizi")
        driveData.append("Hız Analizi")
        driveData.append("Trafik Işığı Analizi")
        driveData.append("Şerit Takip Analizi")
        driveData.append("Nesne Tespit Analizi")
    
        

    }
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return driveData.count
    }
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = UITableViewCell()
        var content = cell.defaultContentConfiguration()
        content.text = driveData[indexPath.row]
        cell.contentConfiguration = content
        return cell
    }
    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        chosenDriveData = driveData[indexPath.row]
        performSegue(withIdentifier: "detailsSegue" , sender: nil)
    }
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        if segue.identifier == "detailsSegue" {
            let destinationVC = segue.destination as! DetailsViewController
            destinationVC.selectedDriveData = chosenDriveData
            
        }
    }
}
