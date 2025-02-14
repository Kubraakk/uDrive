//
//  LoginViewController.swift
//  uDrive
//
//  Created by Kübra AKPUNAR on 15.05.2024.
//

import UIKit


class LoginViewController: UIViewController {

    @IBOutlet weak var loginButton: UIButton!
    
    override func viewDidLoad() {
        super.viewDidLoad()
       
    }
    @IBAction func signClick(_sender: UIButton) {
        performSegue(withIdentifier: "welcomeSegue", sender: self)
    }


}
