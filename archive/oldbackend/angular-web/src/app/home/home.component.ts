import { Component, OnInit, OnDestroy } from '@angular/core';
import {ApiService} from '../api.service';
import { takeUntil } from 'rxjs/operators';
import { HttpResponse } from '@angular/common/http';
import {Subject} from 'rxjs';


export interface Category {
  name: string;
  selected:boolean;
  params?:Category[];
}

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit,OnDestroy {
  destroy$ = new Subject();
  categories: Category[];
  qEvents:any = [];
  results: any;
  constructor(private apiService:ApiService) { }

  ngOnInit(): void {
    // fetch the data from the json-server through the service
    // we use a promised like approach here
    // this.apiService.get().subscribe((data: any[])=>{
    //   console.log(data);
    //   this.results = data;
    //   this.qEvents = this.results.qEvents;
    //   console.log(this.qEvents);
      
    // });
    this.loadParameters();

    // we can now acess the data from the body object of the received http response
    // this.apiService.sendGetRequest().pipe(takeUntil(this.destroy$)).
    // subscribe((res:HttpResponse<any>) =>{
    //   console.log(res);
    //   this.products = res.body;
    // })
  }
  allComplete: boolean = false;

  updateAllComplete() {
    //this.allComplete = this.categories. != null && this.category.categories.every(t => t.selected);
  }

  someComplete(index): boolean {
  //   if (this.categories[index].params == null) {
  //     return false;
  //   }
  //   return this.categories[index].params.filter(t => t.params).length > 0 && !this.allComplete;
    return false;
}

  setAll(completed: boolean) {
    this.allComplete = completed;
    // if (this.category.categories == null) {
    //   return;
    // }
    //this.category.categories.forEach(t => t.selected = completed);
  }
  public loadParameters(){
    this.categories = [{
      name:"Assist1",
      selected:false,
      params: [
        {name: 'assist1', selected: false},
        {name: 'assist2', selected: false},
        ]
      },{
        name:"Assist2",
        selected:false,
        params: [
          {name: 'assist3', selected: false},
          {name: 'assist4', selected: false},
          ]
        },
    ];
  }
  // public firstPage() {
  //   this.products = [];
  //   this.apiService.sendGetRequestToUrl(this.apiService.first).pipe(takeUntil(this.destroy$)).subscribe((res: HttpResponse<any>) => {
  //     console.log(res);
  //     this.products = res.body;
  //   })
  // }
  // public previousPage() {
  //
  //   if (this.apiService.prev !== undefined && this.apiService.prev !== '') {
  //     this.products = [];
  //     this.apiService.sendGetRequestToUrl(this.apiService.prev).pipe(takeUntil(this.destroy$)).subscribe((res: HttpResponse<any>) => {
  //       console.log(res);
  //       this.products = res.body;
  //     })
  //   }
  //
  // }
  // public nextPage() {
  //   if (this.apiService.next !== undefined && this.apiService.next !== '') {
  //     this.products = [];
  //     this.apiService.sendGetRequestToUrl(this.apiService.next).pipe(takeUntil(this.destroy$)).subscribe((res: HttpResponse<any>) => {
  //       console.log(res);
  //       this.products = res.body;
  //     })
  //   }
  // }
  // public lastPage() {
  //   this.products = [];
  //   this.apiService.sendGetRequestToUrl(this.apiService.last).pipe(takeUntil(this.destroy$)).subscribe((res: HttpResponse<any>) => {
  //     console.log(res);
  //     this.products = res.body;
  //   })
  // }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
