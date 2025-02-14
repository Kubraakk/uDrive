//
//  ViewController.swift
//  uDrive
//
//  Created by Kübra AKPUNAR on 15.05.2024.
//

import UIKit

class ViewController: UIViewController {


    @IBOutlet weak var imageView: UIImageView!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        Timer.scheduledTimer(withTimeInterval: 3.0, repeats: false){ timer in
            //timer tetiklendiğinde
            self.performSegue(withIdentifier: "showLoginSegue", sender: self)
        }
        
        let tapGesture = UITapGestureRecognizer(target: self, action: #selector(handleTap))
        self.view.addGestureRecognizer(tapGesture)
    }
    
    @objc func handleTap( _sender: UITapGestureRecognizer){
        //Segueyi tetikle
        self.performSegue(withIdentifier: "showLoginSegue", sender: self)
    }


}

