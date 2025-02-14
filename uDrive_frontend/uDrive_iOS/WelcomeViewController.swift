//
//  WelcomeViewController.swift
//  uDrive
//
//  Created by Kübra AKPUNAR on 16.05.2024.
//

import UIKit

class WelcomeViewController: UIViewController, UITableViewDelegate,UITableViewDataSource {

    @IBOutlet weak var tableView: UITableView!
    var driveDate = [Date]()
    let dateFormatter = DateFormatter()

    
    override func viewDidLoad() {
        super.viewDidLoad()
        //delegasyon ve datasource yetkisini tableViewa self ile veriyoruz.
        tableView.delegate = self
        tableView.dataSource = self
        dateFormatter.dateFormat = "dd/MM/yyyy"
        if let date = dateFormatter.date(from: "22/02/2024") {
            driveDate.append(date)
        } else {
            print("Failed to parse date string")
        }
        

    }
    //delegate ve data source protokolleri için iki fonksiyonu uygulamamız gerekiyor
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return driveDate.count
    }
    //veri
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = UITableViewCell()
        var content = cell.defaultContentConfiguration()
        // Tarih değerini bir dizeye dönüştür
        let dateString = dateFormatter.string(from: driveDate[indexPath.row])
        
        // Dönüştürülmüş dizeyi content.text özelliğine ata
        content.text = dateString
        
        cell.contentConfiguration = content
        return cell

    }
    
    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        performSegue(withIdentifier: "driveSegue" , sender: nil)
    }
    

}
