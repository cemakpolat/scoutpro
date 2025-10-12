import { Injectable } from '@angular/core';
import {HttpClient,HttpErrorResponse, HttpParams} from '@angular/common/http';

// error handling
import {throwError} from 'rxjs';
import {retry,catchError, tap} from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})

export class ApiService {

  //private SERVER_URL = "http://localhost:5000/statistics/";
  private SERVER_URL = "http://127.0.0.1:5000/events/1906061876";
  //private SERVER_URL = "http://localhost:5000/games/";
  //private SERVER_URL = "http://localhost:5000/player";

  public first: string = "";
  public prev: string = "";
  public next: string = "";
  public last: string = "";

  constructor(private httpClient:HttpClient) { }

  public get(){
    return this.httpClient.get(this.SERVER_URL);
  }

  handleError(error:HttpErrorResponse){
    let errorMessage = "Unknown error!";
    if(error.error instanceof ErrorEvent){
      // client-side errors
      errorMessage = `Error:${error.error.message}`;
    }else{
      // server-side errors
      errorMessage = `Error Code: ${error.status}\nMessage:${error.message}`;
    }
    window.alert(errorMessage);
    return throwError(errorMessage);

  }
  // we catch here the error with a custom function
  // public sendGetRequest(){
  //   return this.httpClient.get(this.SERVER_URL).pipe(
  //     catchError(this.handleError)
  //   );
  // }
  // error-handling along with the pagination feature
  public sendGetRequest(){
    // Add safe, URL encoded _page and _limit parameters
    // we added observe option with the response value in the options parameter of the get method so we can
    // have the full HTTP response with headers. NExt, we use the RXJS tap operator for
    //parsing the Link header before returning the final Observable

    // since this function now returns observable with full HTTP respnse, we
    // we need to update the home component.
    return this.httpClient.get(this.SERVER_URL,
      {  params: new HttpParams({fromString: "_page=1&_limit=3"}),
       observe: "response"}).
       pipe(retry(3), catchError(this.handleError), tap(res => {
      console.log(res.headers.get('Link'));
      this.parseLinkHeader(res.headers.get('Link'));
    }));
  }
// tap operator for parsing the Link header before returning the final Observable!
  public sendGetRequestToUrl(url:string){
    return this.httpClient.get(url, {observe:"response"}).pipe(retry(3),
    catchError(this.handleError),tap(res =>{
      console.log(res.headers.get('Link'));
      this.parseLinkHeader(res.headers.get('Link'));
    }));
  }

  parseLinkHeader(header) {
    if (header.length == 0) {
      return ;
    }

    let parts = header.split(',');
    var links = {};
    parts.forEach( p => {
      let section = p.split(';');
      var url = section[0].replace(/<(.*)>/, '$1').trim();
      var name = section[1].replace(/rel="(.*)"/, '$1').trim();
      links[name] = url;

    });

    this.first  = links["first"];
    this.last   = links["last"];
    this.prev   = links["prev"];
    this.next   = links["next"];
  }
}
